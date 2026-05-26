import json
import os
import random
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import F
from core.models import User, Gift, Roulette, RouletteGift, Lottery, LotteryTicket, InventoryItem, Setting, PendingDeposit
from core.decorators import telegram_auth_required

ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(',') if id.strip()]

def get_is_admin(telegram_id):
    return telegram_id in ADMIN_IDS

def index(request):
    return render(request, 'core/index.html')

def profile(request):
    return render(request, 'core/profile.html')

def lottery(request):
    return render(request, 'core/lottery.html')

def admin_panel(request):
    return render(request, 'core/admin.html')

@csrf_exempt
@telegram_auth_required
def auth_user(request):
    if request.method == 'POST':
        user = request.tg_user
        return JsonResponse({
            'user': {
                'telegram_id': user.telegram_id,
                'username': user.username,
                'name': user.name,
                'stars_balance': user.stars_balance,
                'ton_balance': user.ton_balance,
                'is_admin': get_is_admin(user.telegram_id)
            }
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
@telegram_auth_required
def deposit_ton(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.tg_user
        amount_ton = float(data.get('amount_ton', 0))
        boc = data.get('boc')

        if amount_ton <= 0 or not boc:
            return JsonResponse({'error': 'Invalid amount or missing transaction BOC'}, status=400)

        PendingDeposit.objects.create(
            user=user,
            amount_ton=amount_ton,
            boc=boc
        )
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
@telegram_auth_required
def create_stars_invoice(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        stars_amount = int(data.get('amount', 50))

        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            return JsonResponse({'error': 'Bot token not configured'}, status=500)

        payload = {
            'title': 'Top up Stars',
            'description': f'Top up your TopGift balance with {stars_amount} Stars',
            'payload': f'topup_{request.tg_user.telegram_id}_{stars_amount}',
            'provider_token': '',
            'currency': 'XTR',
            'prices': [{'label': 'Stars', 'amount': stars_amount}]
        }

        try:
            r = requests.post(f'https://api.telegram.org/bot{bot_token}/createInvoiceLink', json=payload)
            resp_data = r.json()
            if resp_data.get('ok'):
                return JsonResponse({'success': True, 'invoice_link': resp_data['result']})
            else:
                return JsonResponse({'error': resp_data.get('description', 'Failed to create invoice')}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
@telegram_auth_required
def get_roulettes(request):
    roulettes = Roulette.objects.filter(is_active=True)
    data = [{'id': r.id, 'name': r.name, 'spin_cost': r.spin_cost} for r in roulettes]
    return JsonResponse({'roulettes': data})

@csrf_exempt
@telegram_auth_required
@transaction.atomic
def spin_roulette(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.tg_user
        roulette_id = data.get('roulette_id')

        try:
            user = User.objects.select_for_update().get(id=user.id)
            roulette = Roulette.objects.get(id=roulette_id, is_active=True)

            if user.stars_balance < roulette.spin_cost:
                return JsonResponse({'error': 'Not enough stars'}, status=400)

            user.stars_balance = F('stars_balance') - roulette.spin_cost
            user.save()
            user.refresh_from_db()

            rgifts = RouletteGift.objects.filter(roulette=roulette)
            if not rgifts.exists():
                 return JsonResponse({'error': 'Roulette is empty'}, status=400)

            choices, weights = [], []
            for rg in rgifts:
                choices.append(rg.gift)
                weights.append(rg.chance)

            won_gift = random.choices(choices, weights=weights, k=1)[0]
            InventoryItem.objects.create(user=user, gift=won_gift)

            return JsonResponse({'success': True, 'won_gift': won_gift.name, 'new_balance': user.stars_balance})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
@telegram_auth_required
def get_inventory(request):
    user = request.tg_user
    items = InventoryItem.objects.filter(user=user)
    data = [{'id': item.id, 'gift_name': item.gift.name, 'image': item.gift.image.url if item.gift.image else None, 'status': item.status, 'sell_price': item.gift.sell_price} for item in items]
    return JsonResponse({'inventory': data})

@csrf_exempt
@telegram_auth_required
@transaction.atomic
def sell_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.tg_user
        item_id = data.get('item_id')

        try:
            user = User.objects.select_for_update().get(id=user.id)
            item = InventoryItem.objects.select_for_update().get(id=item_id, user=user, status='in_inventory')

            user.stars_balance = F('stars_balance') + item.gift.sell_price
            user.save()
            user.refresh_from_db()
            item.delete()

            return JsonResponse({'success': True, 'new_balance': user.stars_balance})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@telegram_auth_required
def withdraw_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.tg_user
        item_id = data.get('item_id')
        try:
            item = InventoryItem.objects.get(id=item_id, user=user, status='in_inventory')
            item.status = 'withdraw_pending'
            item.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@telegram_auth_required
def get_lotteries(request):
    lotteries = Lottery.objects.all().order_by('is_finished', '-id')
    data = [{'id': l.id, 'name': l.name, 'image': l.image.url if l.image else None, 'total': l.total_tickets, 'sold': l.sold_tickets, 'cost': l.ticket_cost, 'is_finished': l.is_finished} for l in lotteries]
    return JsonResponse({'lotteries': data})

@csrf_exempt
@telegram_auth_required
@transaction.atomic
def buy_lottery_ticket(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.tg_user
        lottery_id = data.get('lottery_id')

        try:
            user = User.objects.select_for_update().get(id=user.id)
            lottery = Lottery.objects.select_for_update().get(id=lottery_id, is_finished=False)

            if user.stars_balance < lottery.ticket_cost:
                return JsonResponse({'error': 'Not enough stars'}, status=400)

            if lottery.sold_tickets >= lottery.total_tickets:
                return JsonResponse({'error': 'Lottery sold out'}, status=400)

            user.stars_balance = F('stars_balance') - lottery.ticket_cost
            user.save()
            user.refresh_from_db()

            lottery.sold_tickets = F('sold_tickets') + 1
            lottery.save()
            lottery.refresh_from_db()

            LotteryTicket.objects.create(lottery=lottery, user=user, ticket_number=lottery.sold_tickets)

            if lottery.sold_tickets >= lottery.total_tickets:
                lottery.is_finished = True
                lottery.save()

                all_tickets = list(LotteryTicket.objects.filter(lottery=lottery))
                if all_tickets:
                    winners = random.sample(all_tickets, min(lottery.winners_count, len(all_tickets)))
                    for winner_ticket in winners:
                        InventoryItem.objects.create(user=winner_ticket.user, gift=lottery.prize)

            return JsonResponse({'success': True, 'new_balance': user.stars_balance})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@telegram_auth_required
def get_leaderboard(request):
    top_users = User.objects.filter(is_banned=False).order_by('-stars_balance')[:50]
    data = [{'name': u.name or u.username or f"User {u.telegram_id}", 'stars': u.stars_balance} for u in top_users]
    return JsonResponse({'leaderboard': data})

@csrf_exempt
@telegram_auth_required
def get_admin_withdrawals(request):
    user = request.tg_user
    if not get_is_admin(user.telegram_id): return JsonResponse({'error': 'Unauthorized'}, status=403)

    items = InventoryItem.objects.filter(status='withdraw_pending')
    data = [{'id': item.id, 'gift_name': item.gift.name, 'user_name': item.user.name, 'user_tg_id': item.user.telegram_id} for item in items]
    return JsonResponse({'withdrawals': data})

@csrf_exempt
@telegram_auth_required
def fulfill_withdrawal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.tg_user
        item_id = data.get('item_id')

        if not get_is_admin(user.telegram_id): return JsonResponse({'error': 'Unauthorized'}, status=403)

        try:
            item = InventoryItem.objects.get(id=item_id, status='withdraw_pending')
            item.status = 'withdrawn'
            item.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@telegram_auth_required
def admin_manage_entity(request, entity_type):
    user = request.tg_user
    if not get_is_admin(user.telegram_id): return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        if entity_type == 'settings':
            if action == 'update':
                rate = data.get('ton_to_stars_rate')
                Setting.objects.update_or_create(key='ton_to_stars_rate', defaults={'value': str(rate)})
                return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@telegram_auth_required
def admin_manage_users(request):
    user = request.tg_user
    if not get_is_admin(user.telegram_id): return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'GET':
        users = list(User.objects.values('id', 'telegram_id', 'username', 'name', 'is_banned', 'stars_balance'))
        return JsonResponse({'users': users})

    elif request.method == 'POST':
        data = json.loads(request.body)
        target = User.objects.get(id=data['id'])
        target.is_banned = data['is_banned']
        target.save()
        return JsonResponse({'success': True})

@csrf_exempt
@telegram_auth_required
def admin_manage_gifts(request):
    user = request.tg_user
    if not get_is_admin(user.telegram_id): return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'GET':
        gifts = list(Gift.objects.values('id', 'name', 'display_price', 'sell_price', 'image'))
        for g in gifts:
            if g['image']: g['image'] = '/media/' + g['image']
        return JsonResponse({'gifts': gifts})

    elif request.method == 'POST':
        name = request.POST.get('name')
        display_price = request.POST.get('display_price')
        sell_price = request.POST.get('sell_price')
        image = request.FILES.get('image')

        if not name or not display_price or not sell_price:
             return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            gift = Gift.objects.create(name=name, display_price=display_price, sell_price=sell_price, image=image)
            return JsonResponse({'success': True, 'id': gift.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@telegram_auth_required
def admin_manage_roulettes(request):
    user = request.tg_user
    if not get_is_admin(user.telegram_id): return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'GET':
        rs = Roulette.objects.all()
        data = []
        for r in rs:
            gifts = list(r.gifts.values('gift__name', 'chance'))
            data.append({'id': r.id, 'name': r.name, 'spin_cost': r.spin_cost, 'is_active': r.is_active, 'gifts': gifts})
        return JsonResponse({'roulettes': data})

    elif request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        spin_cost = data.get('spin_cost')
        gifts_data = data.get('gifts', [])

        if not name or not spin_cost:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            r = Roulette.objects.create(name=name, spin_cost=spin_cost)
            for gd in gifts_data:
                g = Gift.objects.get(id=gd['gift_id'])
                RouletteGift.objects.create(roulette=r, gift=g, chance=gd['chance'])
            return JsonResponse({'success': True, 'id': r.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@telegram_auth_required
def admin_manage_lotteries(request):
    user = request.tg_user
    if not get_is_admin(user.telegram_id): return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'GET':
        ls = Lottery.objects.all()
        data = []
        for l in ls:
            data.append({'id': l.id, 'name': l.name, 'total_tickets': l.total_tickets, 'ticket_cost': l.ticket_cost, 'prize': l.prize.name, 'is_finished': l.is_finished})
        return JsonResponse({'lotteries': data})

    elif request.method == 'POST':
        name = request.POST.get('name')
        total_tickets = request.POST.get('total_tickets')
        ticket_cost = request.POST.get('ticket_cost')
        prize_id = request.POST.get('prize_id')
        winners_count = request.POST.get('winners_count', 1)
        image = request.FILES.get('image')

        if not name or not total_tickets or not ticket_cost or not prize_id:
             return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            l = Lottery.objects.create(name=name, total_tickets=total_tickets, ticket_cost=ticket_cost, prize_id=prize_id, winners_count=winners_count, image=image)
            return JsonResponse({'success': True, 'id': l.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@telegram_auth_required
def admin_manage_deposits(request):
    user = request.tg_user
    if not get_is_admin(user.telegram_id): return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'GET':
        deposits = PendingDeposit.objects.filter(is_processed=False)
        data = [{'id': d.id, 'user_name': d.user.name, 'amount_ton': d.amount_ton, 'boc': d.boc, 'date': d.created_at} for d in deposits]
        return JsonResponse({'deposits': data})

    elif request.method == 'POST':
        data = json.loads(request.body)
        dep_id = data.get('deposit_id')

        try:
            with transaction.atomic():
                d = PendingDeposit.objects.select_for_update().get(id=dep_id, is_processed=False)
                d.is_processed = True
                d.save()

                target_user = User.objects.select_for_update().get(id=d.user.id)

                rate_setting = Setting.objects.filter(key='ton_to_stars_rate').first()
                rate = float(rate_setting.value) if rate_setting else 1000.0
                stars_to_credit = int(d.amount_ton * rate)

                target_user.ton_balance = F('ton_balance') + d.amount_ton
                target_user.stars_balance = F('stars_balance') + stars_to_credit
                target_user.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
