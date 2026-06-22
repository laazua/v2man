from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import InviteCode, Referral, Withdrawal, SystemSetting
from .serializers import InviteCodeSerializer, ReferralSerializer, WithdrawalSerializer, AdminWithdrawalSerializer, SystemSettingSerializer
from users.wallet import Wallet


class GenerateInviteCodeView(APIView):
    def post(self, request):
        code = InviteCode.objects.create(owner=request.user)
        serializer = InviteCodeSerializer(code)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ListInviteCodesView(generics.ListAPIView):
    serializer_class = InviteCodeSerializer

    def get_queryset(self):
        return InviteCode.objects.filter(owner=self.request.user)


class ListReferralsView(generics.ListAPIView):
    serializer_class = ReferralSerializer

    def get_queryset(self):
        return Referral.objects.filter(inviter=self.request.user)


class EarningsView(APIView):
    def get(self, request):
        referrals = Referral.objects.filter(inviter=request.user)
        total_earned = sum(r.earned for r in referrals)
        return Response({
            'total_earned': total_earned,
            'total_referees': referrals.count(),
            'percentage': SystemSetting.get_int('referral_percentage', 20),
        })


class CreateWithdrawalView(APIView):
    def post(self, request):
        try:
            amount = int(request.data.get('amount', 0))
        except (ValueError, TypeError):
            return Response({'error': '无效金额'}, status=status.HTTP_400_BAD_REQUEST)
        if amount < 1:
            return Response({'error': '无效金额'}, status=status.HTTP_400_BAD_REQUEST)

        min_amount = SystemSetting.get_int('withdrawal_min', 3000)
        if amount < min_amount:
            return Response({'error': f'最低提现金额为 ¥{min_amount / 100:.2f}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return Response({'error': '钱包不存在'}, status=status.HTTP_400_BAD_REQUEST)

        if wallet.balance < amount:
            return Response({'error': '余额不足'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=request.user)
            if wallet.balance < amount:
                return Response({'error': '余额不足'}, status=status.HTTP_400_BAD_REQUEST)
            wallet.balance -= amount
            wallet.save()
            w = Withdrawal.objects.create(user=request.user, amount=amount)

        return Response(WithdrawalSerializer(w).data, status=status.HTTP_201_CREATED)


class ListWithdrawalsView(generics.ListAPIView):
    serializer_class = WithdrawalSerializer

    def get_queryset(self):
        return Withdrawal.objects.filter(user=self.request.user)


class SettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        settings = SystemSetting.objects.all()
        serializer = SystemSettingSerializer(settings, many=True)
        data = {s['key']: s['value'] for s in serializer.data}
        data.setdefault('referral_percentage', '20')
        data.setdefault('withdrawal_min', '3000')
        return Response(data)

    def put(self, request):
        for key, value in request.data.items():
            SystemSetting.objects.update_or_create(key=key, defaults={'value': str(value)})
        return Response({'success': True})


class AdminWithdrawalListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminWithdrawalSerializer
    queryset = Withdrawal.objects.all()


class AdminWithdrawalActionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        from django.utils import timezone
        try:
            w = Withdrawal.objects.get(id=pk, status=Withdrawal.PENDING)
        except Withdrawal.DoesNotExist:
            return Response({'error': '提现申请不存在或已处理'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action == 'approve':
            w.status = Withdrawal.APPROVED
        elif action == 'reject':
            w.status = Withdrawal.REJECTED
            wallet = Wallet.objects.get(user=w.user)
            wallet.balance += w.amount
            wallet.save()
        else:
            return Response({'error': '无效操作'}, status=status.HTTP_400_BAD_REQUEST)

        w.processed_at = timezone.now()
        w.note = request.data.get('note', '')
        w.save()
        return Response({'success': True})
