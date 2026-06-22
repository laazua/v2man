from abc import ABC, abstractmethod

from django.conf import settings


class PaymentDriver(ABC):
    @abstractmethod
    def create_order(self, request, user, amount: int, out_trade_no: str) -> dict:
        pass

    @abstractmethod
    def verify_notification(self, request) -> dict | None:
        pass


class SimulateDriver(PaymentDriver):
    def create_order(self, request, user, amount, out_trade_no):
        return {'out_trade_no': out_trade_no}

    def verify_notification(self, request):
        import time
        out_trade_no = request.data.get('out_trade_no', '')
        trade_no = request.data.get('trade_no', f'SIM{int(time.time())}')
        return {'out_trade_no': out_trade_no, 'trade_no': trade_no}


class AlipayDriver(PaymentDriver):
    def __init__(self, app_id, private_key, alipay_public_key, notify_url):
        self.app_id = app_id
        self.private_key = private_key
        self.alipay_public_key = alipay_public_key
        self.notify_url = notify_url

    def _get_alipay(self):
        try:
            from alipay import AliPay
        except ImportError:
            raise ImportError(
                '请安装 alipay-sdk-python: uv add alipay-sdk-python'
            )
        return AliPay(
            appid=self.app_id,
            app_notify_url=self.notify_url,
            app_private_key_string=self.private_key,
            alipay_public_key_string=self.alipay_public_key,
            sign_type='RSA2',
            debug=settings.DEBUG,
        )

    def create_order(self, request, user, amount, out_trade_no):
        alipay = self._get_alipay()
        result = alipay.api_alipay_trade_precreate(
            out_trade_no=out_trade_no,
            total_amount=f'{amount / 100:.2f}',
            subject='v2man 充值',
        )
        if result.get('code') == '10000' and result.get('msg') == 'Success':
            return {
                'out_trade_no': out_trade_no,
                'qr_code': result.get('qr_code', ''),
            }
        error = result.get('sub_msg', result.get('msg', '未知错误'))
        raise Exception(f'支付宝下单失败: {error}')

    def verify_notification(self, request):
        alipay = self._get_alipay()
        data = request.data.copy()
        signature = data.pop('sign', '')
        if not alipay.verify(data, signature):
            return None
        return {
            'out_trade_no': data.get('out_trade_no'),
            'trade_no': data.get('trade_no'),
        }


def get_payment_driver(request=None):
    from invite.models import SystemSetting

    driver_name = SystemSetting.get('payment_driver', 'simulate')

    if driver_name == 'alipay':
        app_id = SystemSetting.get('alipay_app_id', '')
        private_key = SystemSetting.get('alipay_private_key', '')
        alipay_public_key = SystemSetting.get('alipay_public_key', '')
        notify_url = ''
        if request:
            notify_url = request.build_absolute_uri('/api/auth/payment/notify/')
        return AlipayDriver(
            app_id=app_id,
            private_key=private_key,
            alipay_public_key=alipay_public_key,
            notify_url=notify_url,
        )

    return SimulateDriver()
