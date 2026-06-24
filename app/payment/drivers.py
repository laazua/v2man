"""支付驱动：模拟支付与支付宝。"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from django.conf import settings

logger = logging.getLogger("business")


class PaymentDriver(ABC):
    """支付驱动抽象基类。"""

    @abstractmethod
    def create_order(
        self,
        request: Any,
        user: Any,
        amount: int,
        out_trade_no: str,
    ) -> dict:
        """创建支付订单。

        request 参数可能是 DRF Request 或 Django HttpRequest，
        由调用方传入，此处统一使用 Any。
        """
        pass

    @abstractmethod
    def verify_notification(
        self,
        request: Any,
    ) -> Optional[dict]:
        """验证支付回调通知。"""
        pass


class SimulateDriver(PaymentDriver):
    """模拟支付驱动，用于开发测试。"""

    def create_order(
        self,
        request: Any,
        user: Any,
        amount: int,
        out_trade_no: str,
    ) -> dict:
        logger.info(
            "模拟支付下单: user_id=%s amount=%s out_trade_no=%s",
            user.id,
            amount,
            out_trade_no,
        )
        return {"out_trade_no": out_trade_no}

    def verify_notification(
        self,
        request: Any,
    ) -> Optional[dict]:
        import time

        out_trade_no = request.data.get("out_trade_no", "")
        trade_no = request.data.get(
            "trade_no",
            f"SIM{int(time.time())}",
        )
        logger.info(
            "模拟支付验签: out_trade_no=%s trade_no=%s",
            out_trade_no,
            trade_no,
        )
        return {"out_trade_no": out_trade_no, "trade_no": trade_no}


class AlipayDriver(PaymentDriver):
    """支付宝支付驱动。"""

    def __init__(
        self,
        app_id: str,
        private_key: str,
        alipay_public_key: str,
        notify_url: str,
    ) -> None:
        self.app_id = app_id
        self.private_key = private_key
        self.alipay_public_key = alipay_public_key
        self.notify_url = notify_url

    def _get_alipay(self) -> Any:
        try:
            from alipay import AliPay
        except ImportError:
            raise ImportError(
                "请安装 alipay-sdk-python: uv add alipay-sdk-python",
            )
        return AliPay(
            appid=self.app_id,
            app_notify_url=self.notify_url,
            app_private_key_string=self.private_key,
            alipay_public_key_string=self.alipay_public_key,
            sign_type="RSA2",
            debug=settings.DEBUG,
        )

    def create_order(
        self,
        request: Any,
        user: Any,
        amount: int,
        out_trade_no: str,
    ) -> dict:
        alipay = self._get_alipay()
        result = alipay.api_alipay_trade_precreate(
            out_trade_no=out_trade_no,
            total_amount=f"{amount / 100:.2f}",
            subject="v2man 充值",
        )
        if result.get("code") == "10000" and result.get("msg") == "Success":
            logger.info(
                "支付宝下单成功: user_id=%s amount=%s out_trade_no=%s",
                user.id,
                amount,
                out_trade_no,
            )
            return {
                "out_trade_no": out_trade_no,
                "qr_code": result.get("qr_code", ""),
            }
        error = result.get("sub_msg", result.get("msg", "未知错误"))
        logger.error(
            "支付宝下单失败: user_id=%s amount=%s error=%s",
            user.id,
            amount,
            error,
        )
        raise Exception(f"支付宝下单失败: {error}")

    def verify_notification(
        self,
        request: Any,
    ) -> Optional[dict]:
        alipay = self._get_alipay()
        data = request.data.copy()
        signature = data.pop("sign", "")
        if not alipay.verify(data, signature):
            logger.warning(
                "支付宝验签失败: out_trade_no=%s",
                data.get("out_trade_no", ""),
            )
            return None
        logger.info(
            "支付宝验签成功: out_trade_no=%s trade_no=%s",
            data.get("out_trade_no"),
            data.get("trade_no"),
        )
        return {
            "out_trade_no": data.get("out_trade_no"),
            "trade_no": data.get("trade_no"),
        }


def get_payment_driver(request: Any = None) -> PaymentDriver:
    """根据系统设置获取支付驱动实例。"""
    from invite.models import SystemSetting

    driver_name = SystemSetting.get("payment_driver", "simulate")
    logger.info("获取支付驱动: driver=%s", driver_name)

    if driver_name == "alipay":
        app_id = SystemSetting.get("alipay_app_id", "")
        private_key = SystemSetting.get("alipay_private_key", "")
        alipay_public_key = SystemSetting.get("alipay_public_key", "")
        notify_url = ""
        if request:
            notify_url = request.build_absolute_uri(
                "/api/auth/payment/notify/",
            )
        masked = (app_id[:6] + "***") if app_id else ""
        logger.info(
            "支付宝驱动初始化: app_id=%s notify_url=%s",
            masked,
            notify_url,
        )
        return AlipayDriver(
            app_id=app_id,
            private_key=private_key,
            alipay_public_key=alipay_public_key,
            notify_url=notify_url,
        )

    return SimulateDriver()
