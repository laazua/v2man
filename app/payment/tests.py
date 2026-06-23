"""支付驱动模块测试。"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from payment.drivers import (
    AlipayDriver,
    PaymentDriver,
    SimulateDriver,
    get_payment_driver,
)


class PaymentDriverAbstractTests(TestCase):
    """PaymentDriver 抽象基类测试。"""

    def test_cannot_instantiate_abstract_class(self) -> None:
        with self.assertRaises(TypeError):
            PaymentDriver()  # type: ignore[abstract]

    def test_has_abstract_methods(self) -> None:
        abstract_methods = {
            name
            for name, method in PaymentDriver.__dict__.items()
            if getattr(method, '__isabstractmethod__', False)
        }
        self.assertIn('create_order', abstract_methods)
        self.assertIn('verify_notification', abstract_methods)


class SimulateDriverTests(TestCase):
    """SimulateDriver 测试。"""

    def setUp(self) -> None:
        self.driver = SimulateDriver()

    def test_create_order_returns_out_trade_no(self) -> None:
        result = self.driver.create_order(
            request=MagicMock(),
            user=MagicMock(id=1),
            amount=100,
            out_trade_no='TEST20250101001',
        )
        self.assertIn('out_trade_no', result)
        self.assertEqual(result['out_trade_no'], 'TEST20250101001')

    def test_verify_notification_returns_data(self) -> None:
        request = MagicMock()
        request.data = {
            'out_trade_no': 'TEST20250101001',
        }
        result = self.driver.verify_notification(request)
        self.assertIsNotNone(result)
        self.assertEqual(result['out_trade_no'], 'TEST20250101001')
        self.assertIn('trade_no', result)
        self.assertTrue(result['trade_no'].startswith('SIM'))

    def test_verify_notification_without_out_trade_no(self) -> None:
        request = MagicMock()
        request.data = {}
        result = self.driver.verify_notification(request)
        self.assertIsNotNone(result)
        self.assertEqual(result['out_trade_no'], '')
        self.assertIn('trade_no', result)


class AlipayDriverTests(TestCase):
    """AlipayDriver 测试。"""

    def setUp(self) -> None:
        self.driver = AlipayDriver(
            app_id='2021001001',
            private_key='fake-private-key',
            alipay_public_key='fake-public-key',
            notify_url='https://example.com/notify/',
        )
        self.mock_alipay = MagicMock()
        self.driver._get_alipay = MagicMock(return_value=self.mock_alipay)

    def test_create_order_returns_qr_code(self) -> None:
        self.mock_alipay.api_alipay_trade_precreate.return_value = {
            'code': '10000',
            'msg': 'Success',
            'qr_code': 'https://qr.alipay.com/test',
        }

        result = self.driver.create_order(
            request=MagicMock(),
            user=MagicMock(id=1),
            amount=5000,
            out_trade_no='ALI20250101001',
        )
        self.assertEqual(result['out_trade_no'], 'ALI20250101001')
        self.assertEqual(result['qr_code'], 'https://qr.alipay.com/test')
        self.mock_alipay.api_alipay_trade_precreate.assert_called_once_with(
            out_trade_no='ALI20250101001',
            total_amount='50.00',
            subject='v2man 充值',
        )

    def test_create_order_failure_raises_exception(self) -> None:
        self.mock_alipay.api_alipay_trade_precreate.return_value = {
            'code': '40004',
            'msg': 'Business Failed',
            'sub_msg': '余额不足',
        }

        with self.assertRaises(Exception) as ctx:
            self.driver.create_order(
                request=MagicMock(),
                user=MagicMock(id=1),
                amount=5000,
                out_trade_no='ALI20250101001',
            )
        self.assertIn('余额不足', str(ctx.exception))

    def test_verify_notification_success(self) -> None:
        self.mock_alipay.verify.return_value = True

        request = MagicMock()
        request.data = {
            'out_trade_no': 'ALI20250101001',
            'trade_no': '2025010120001001',
            'sign': 'valid-signature',
        }

        result = self.driver.verify_notification(request)
        self.assertIsNotNone(result)
        self.assertEqual(result['out_trade_no'], 'ALI20250101001')
        self.assertEqual(result['trade_no'], '2025010120001001')
        self.mock_alipay.verify.assert_called_once()

    def test_verify_notification_failure_returns_none(self) -> None:
        self.mock_alipay.verify.return_value = False

        request = MagicMock()
        request.data = {
            'out_trade_no': 'ALI20250101001',
            'sign': 'bad-signature',
        }

        result = self.driver.verify_notification(request)
        self.assertIsNone(result)

    def test_import_error_when_sdk_not_installed(self) -> None:
        import sys
        import types
        fresh_driver = AlipayDriver(
            app_id='test', private_key='pk',
            alipay_public_key='apk', notify_url='',
        )
        mock_alipay_module = types.ModuleType('alipay')
        with patch.dict('sys.modules', {'alipay': mock_alipay_module}):
            with self.assertRaises(ImportError):
                fresh_driver._get_alipay()


class GetPaymentDriverTests(TestCase):
    """get_payment_driver 工厂函数测试。"""

    def setUp(self) -> None:
        from invite.models import SystemSetting
        SystemSetting.objects.all().delete()

    def test_default_returns_simulate(self) -> None:
        driver = get_payment_driver()
        self.assertIsInstance(driver, SimulateDriver)

    def test_simulate_setting(self) -> None:
        from invite.models import SystemSetting
        SystemSetting.objects.create(
            key='payment_driver', value='simulate',
        )
        driver = get_payment_driver()
        self.assertIsInstance(driver, SimulateDriver)

    def test_alipay_setting_without_settings_returns_alipay_driver(
        self,
    ) -> None:
        from invite.models import SystemSetting
        SystemSetting.objects.create(
            key='payment_driver', value='alipay',
        )
        driver = get_payment_driver()
        self.assertIsInstance(driver, AlipayDriver)

    def test_alipay_with_full_config(self) -> None:
        from invite.models import SystemSetting
        SystemSetting.objects.create(
            key='payment_driver', value='alipay',
        )
        SystemSetting.objects.create(
            key='alipay_app_id', value='2021001001',
        )
        SystemSetting.objects.create(
            key='alipay_private_key', value='private-key',
        )
        SystemSetting.objects.create(
            key='alipay_public_key', value='public-key',
        )

        request = MagicMock()
        request.build_absolute_uri.return_value = (
            'https://example.com/api/auth/payment/notify/'
        )
        driver = get_payment_driver(request)
        self.assertIsInstance(driver, AlipayDriver)
        self.assertEqual(driver.app_id, '2021001001')
        self.assertEqual(driver.private_key, 'private-key')
        self.assertEqual(driver.alipay_public_key, 'public-key')
        self.assertEqual(
            driver.notify_url,
            'https://example.com/api/auth/payment/notify/',
        )
