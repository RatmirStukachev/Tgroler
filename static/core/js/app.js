// Initialize Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();

// Helper to get auth header
function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-TG-INIT-DATA': tg.initData || "test_mode"
    };
}

let currentUser = null;

// Mock user data for testing outside Telegram
const initData = tg.initDataUnsafe.user ? tg.initDataUnsafe : {
    user: { id: 123456789, first_name: "TestUser", username: "test_user" }
};

// TON Connect Initialization
let tonConnectUI = null;
if (document.getElementById('ton-connect')) {
    tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
        manifestUrl: 'https://raw.githubusercontent.com/ton-community/tutorials/main/03-client/test/public/tonconnect-manifest.json',
        buttonRootId: 'ton-connect'
    });
}

// Auth function
async function authenticateUser() {
    try {
        const res = await fetch('/api/auth/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({})
        });
        const data = await res.json();
        currentUser = data.user;
        updateUI();

        if(currentUser.is_admin) {
            const nav = document.querySelector('.bottom-nav');
            if(nav && !document.getElementById('nav-admin')) {
                nav.innerHTML += `<a href="/admin-panel/" id="nav-admin" class="nav-item">Admin</a>`;
            }
        }

        // Route to specific page logic
        if(window.location.pathname === '/') loadRouletteList();
        if(window.location.pathname === '/profile/') {
            loadInventory();
            loadLeaderboard();
        }
        if(window.location.pathname === '/lottery/') loadLotteries();
        if(window.location.pathname === '/admin-panel/') loadAdminWithdrawals();

    } catch (e) {
        console.error("Auth failed:", e);
    }
}

function updateUI() {
    if(!currentUser) return;
    const sBal = document.getElementById('user-stars-balance');
    const tBal = document.getElementById('user-ton-balance');
    const pName = document.getElementById('profile-name');
    const pId = document.getElementById('profile-id');

    if(sBal) sBal.innerText = currentUser.stars_balance;
    if(tBal) tBal.innerText = currentUser.ton_balance.toFixed(2);
    if(pName) pName.innerText = currentUser.name;
    if(pId) pId.innerText = currentUser.telegram_id;
}

// --- ROULETTE ---
async function loadRouletteList() {
    try {
        const res = await fetch('/api/roulettes/', { headers: getAuthHeaders() });
        const data = await res.json();
        const sel = document.getElementById('roulette-selector');
        if(!sel) return;

        data.roulettes.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.dataset.cost = r.spin_cost;
            opt.innerText = r.name;
            sel.appendChild(opt);
        });
    } catch(e) { console.error(e); }
}

function loadRoulette() {
    const sel = document.getElementById('roulette-selector');
    const display = document.getElementById('roulette-display');
    const val = sel.value;

    if(!val) {
        display.style.display = 'none';
        return;
    }

    const opt = sel.options[sel.selectedIndex];
    document.getElementById('roulette-name').innerText = opt.innerText;
    document.getElementById('roulette-cost').innerText = opt.dataset.cost;
    document.getElementById('spin-result').innerText = '';
    display.style.display = 'block';
}

async function spinRoulette() {
    const sel = document.getElementById('roulette-selector');
    const rouletteId = sel.value;
    const resEl = document.getElementById('spin-result');

    resEl.innerText = "Spinning...";
    resEl.style.color = "gold";

    try {
        const res = await fetch('/api/spin/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ roulette_id: rouletteId })
        });
        const data = await res.json();

        if(data.error) {
            resEl.innerText = data.error;
            resEl.style.color = "red";
        } else {
            resEl.innerText = `You won: ${data.won_gift}! 🎉`;
            resEl.style.color = "lime";
            currentUser.stars_balance = data.new_balance;
            updateUI();
        }
    } catch(e) {
        resEl.innerText = "Error spinning";
        resEl.style.color = "red";
    }
}

// --- INVENTORY (Profile) ---
async function loadInventory() {
    const grid = document.getElementById('inventory-grid');
    if(!grid) return;

    grid.innerHTML = "Loading...";
    try {
        const res = await fetch('/api/inventory/', { headers: getAuthHeaders() });
        const data = await res.json();

        grid.innerHTML = '';
        data.inventory.forEach(item => {
            let btns = '';
            if(item.status === 'in_inventory') {
                btns = `
                    <button class="btn btn-accent" onclick="sellItem(${item.id})">Sell (${item.sell_price}⭐)</button>
                    <button class="btn" onclick="withdrawItem(${item.id})">Withdraw</button>
                `;
            } else if (item.status === 'withdraw_pending') {
                btns = `<p style="color:orange;">Withdraw Pending...</p>`;
            } else {
                btns = `<p style="color:lime;">Withdrawn</p>`;
            }

            grid.innerHTML += `
                <div class="card">
                    ${item.image ? `<img src="${item.image}" alt="gift">` : '🎁'}
                    <h4>${item.gift_name}</h4>
                    ${btns}
                </div>
            `;
        });
    } catch(e) { console.error(e); }
}

async function sellItem(id) {
    if(!confirm("Sell this item?")) return;
    try {
        const res = await fetch('/api/sell/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();
        if(data.success) {
            currentUser.stars_balance = data.new_balance;
            updateUI();
            loadInventory();
        } else { alert(data.error); }
    } catch(e) { console.error(e); }
}

async function withdrawItem(id) {
    if(!confirm("Withdraw this item?")) return;
    try {
        const res = await fetch('/api/withdraw/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();
        if(data.success) {
            loadInventory();
            tg.showAlert("Withdrawal requested! Admin will process it soon.");
        } else { alert(data.error); }
    } catch(e) { console.error(e); }
}

// --- LOTTERY ---
async function loadLotteries() {
    const list = document.getElementById('lottery-list');
    if(!list) return;

    list.innerHTML = "Loading...";
    try {
        const res = await fetch('/api/lotteries/', { headers: getAuthHeaders() });
        const data = await res.json();

        list.innerHTML = '';
        data.lotteries.forEach(l => {
            const statusStr = l.is_finished ? "Finished" : `${l.sold}/${l.total} tickets sold`;
            const btnStr = l.is_finished ? `<button class="btn" disabled>Finished</button>` : `<button class="btn btn-accent" onclick="buyTicket(${l.id})">Buy Ticket (${l.cost}⭐)</button>`;

            list.innerHTML += `
                <div class="card" style="margin-bottom: 15px; text-align: left; display:flex; align-items:center;">
                    <div style="flex:1;">
                        <h3>${l.name}</h3>
                        <p style="color:#aaa;">${statusStr}</p>
                        ${btnStr}
                    </div>
                </div>
            `;
        });
    } catch(e) { console.error(e); }
}

async function buyTicket(id) {
    try {
        const res = await fetch('/api/lotteries/buy/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ lottery_id: id })
        });
        const data = await res.json();
        if(data.success) {
            currentUser.stars_balance = data.new_balance;
            updateUI();
            loadLotteries();
            tg.showAlert("Ticket purchased!");
        } else { alert(data.error); }
    } catch(e) { console.error(e); }
}

// --- ADMIN ---
async function loadAdminWithdrawals() {
    const list = document.getElementById('withdrawals-list');
    if(!list) return;

    list.innerHTML = "Loading...";
    try {
        const res = await fetch('/api/admin/withdrawals/', { headers: getAuthHeaders() });
        const data = await res.json();

        list.innerHTML = '';
        if(data.error) { list.innerHTML = escapeHTML(data.error); return; }

        if(data.withdrawals.length === 0) { list.innerHTML = "No pending withdrawals."; }

        data.withdrawals.forEach(w => {
            list.innerHTML += `
                <div class="card" style="margin-bottom: 10px; border: 1px solid #333;">
                    <p><strong>Item:</strong> ${escapeHTML(w.gift_name)}</p>
                    <p><strong>User:</strong> ${escapeHTML(w.user_name)} (ID: ${w.user_tg_id})</p>
                    <button class="btn btn-accent" onclick="fulfillWithdrawal(${w.id})">Mark as Fulfilled</button>
                </div>
            `;
        });
    } catch(e) { console.error(e); }
}

async function fulfillWithdrawal(id) {
    try {
        const res = await fetch('/api/admin/fulfill/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();
        if(data.success) {
            loadAdminWithdrawals();
        } else { alert(data.error); }
    } catch(e) { console.error(e); }
}

async function saveSettings() {
    const rate = document.getElementById('setting-rate').value;
    if(!rate) return;

    try {
        const res = await fetch('/api/admin/settings/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ action: 'update', ton_to_stars_rate: rate })
        });
        const data = await res.json();
        if(data.success) alert("Settings saved!");
    } catch(e) { console.error(e); }
}

document.addEventListener('DOMContentLoaded', () => {
    authenticateUser();
});

// --- ADMIN EXPANDED ---
async function loadAdminUsers() {
    const list = document.getElementById('users-list');
    if(!list) return;
    list.innerHTML = "Loading...";
    try {
        const res = await fetch('/api/admin/users/', { headers: getAuthHeaders() });
        const data = await res.json();
        list.innerHTML = '';
        data.users.forEach(u => {
            const banBtn = `<button class="btn ${u.is_banned ? 'btn-accent' : 'btn-danger'}" onclick="toggleBan(${u.id}, ${!u.is_banned})">${u.is_banned ? 'Unban' : 'Ban'}</button>`;
            list.innerHTML += `
                <div class="card" style="margin-bottom: 10px; text-align:left;">
                    <p><strong>${escapeHTML(u.name)}</strong> (@${escapeHTML(u.username)})</p>
                    <p>Stars: ${u.stars_balance} | Banned: ${u.is_banned}</p>
                    ${banBtn}
                </div>
            `;
        });
    } catch(e) { console.error(e); }
}

async function toggleBan(id, is_banned) {
    try {
        await fetch('/api/admin/users/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ id, is_banned })
        });
        loadAdminUsers();
    } catch(e) { console.error(e); }
}

let cachedGifts = [];
async function loadAdminGifts() {
    const list = document.getElementById('gifts-list');
    if(!list) return;
    list.innerHTML = "Loading...";
    try {
        const res = await fetch('/api/admin/gifts/', { headers: getAuthHeaders() });
        const data = await res.json();
        cachedGifts = data.gifts;
        list.innerHTML = '';
        data.gifts.forEach(g => {
            list.innerHTML += `
                <div class="card">
                    ${g.image ? `<img src="${g.image}" style="max-height:80px">` : '🎁'}
                    <p>${g.name}</p>
                    <small>Disp: ${g.display_price} | Sell: ${g.sell_price}</small>
                </div>
            `;
        });

        // Update selectors in other tabs
        const rSel = document.getElementById('r-gift-selector');
        if(rSel) {
            rSel.innerHTML = '';
            cachedGifts.forEach(g => {
                rSel.innerHTML += `
                    <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                        <label><input type="checkbox" class="r-gift-cb" value="${g.id}"> ${g.name}</label>
                        <input type="number" id="r-chance-${g.id}" placeholder="Chance %" style="width: 80px; margin:0;">
                    </div>
                `;
            });
        }

        const lPrize = document.getElementById('l-prize');
        if(lPrize) {
            lPrize.innerHTML = '<option value="">Select Prize...</option>';
            cachedGifts.forEach(g => {
                lPrize.innerHTML += `<option value="${g.id}">${g.name}</option>`;
            });
        }
    } catch(e) { console.error(e); }
}

async function createGift() {
    const fd = new FormData();
    fd.append('name', document.getElementById('gift-name').value);
    fd.append('display_price', document.getElementById('gift-dprice').value);
    fd.append('sell_price', document.getElementById('gift-sprice').value);
    const f = document.getElementById('gift-img').files[0];
    if(f) fd.append('image', f);

    // Custom auth header approach for FormData
    const hdrs = getAuthHeaders();
    delete hdrs['Content-Type']; // Let browser set boundary

    try {
        const res = await fetch('/api/admin/gifts/', {
            method: 'POST',
            headers: hdrs,
            body: fd
        });
        await res.json();
        document.getElementById('gift-name').value = '';
        loadAdminGifts();
    } catch(e) { console.error(e); }
}

async function loadAdminRoulettes() {
    const list = document.getElementById('roulettes-list');
    if(!list) return;
    list.innerHTML = "Loading...";
    try {
        const res = await fetch('/api/admin/roulettes/', { headers: getAuthHeaders() });
        const data = await res.json();
        list.innerHTML = '';
        data.roulettes.forEach(r => {
            const giftsStr = r.gifts.map(g => `${g.gift__name}(${g.chance}%)`).join(', ');
            list.innerHTML += `
                <div class="card" style="margin-bottom:10px; text-align:left;">
                    <h4>${r.name} (Cost: ${r.spin_cost}⭐)</h4>
                    <p style="font-size:12px; color:#aaa;">Gifts: ${giftsStr}</p>
                </div>
            `;
        });
    } catch(e) { console.error(e); }
}

async function createRoulette() {
    const name = document.getElementById('r-name').value;
    const cost = document.getElementById('r-cost').value;

    const gifts = [];
    document.querySelectorAll('.r-gift-cb:checked').forEach(cb => {
        const gid = cb.value;
        const chance = document.getElementById('r-chance-' + gid).value;
        if(chance) gifts.push({ gift_id: gid, chance: parseFloat(chance) });
    });

    try {
        await fetch('/api/admin/roulettes/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ name, spin_cost: cost, gifts })
        });
        loadAdminRoulettes();
    } catch(e) { console.error(e); }
}

async function loadAdminLotteries() {
    const list = document.getElementById('lotteries-list');
    if(!list) return;
    list.innerHTML = "Loading...";
    try {
        const res = await fetch('/api/admin/lotteries/', { headers: getAuthHeaders() });
        const data = await res.json();
        list.innerHTML = '';
        data.lotteries.forEach(l => {
            list.innerHTML += `
                <div class="card" style="margin-bottom:10px; text-align:left;">
                    <h4>${l.name}</h4>
                    <p>Total: ${l.total_tickets} | Cost: ${l.ticket_cost}⭐</p>
                    <p>Prize: ${l.prize} | Finished: ${l.is_finished}</p>
                </div>
            `;
        });
    } catch(e) { console.error(e); }
}

async function createLottery() {
    const fd = new FormData();
    fd.append('name', document.getElementById('l-name').value);
    fd.append('total_tickets', document.getElementById('l-total').value);
    fd.append('ticket_cost', document.getElementById('l-cost').value);
    fd.append('prize_id', document.getElementById('l-prize').value);
    const f = document.getElementById('l-img').files[0];
    if(f) fd.append('image', f);

    const hdrs = getAuthHeaders();
    delete hdrs['Content-Type'];

    try {
        await fetch('/api/admin/lotteries/', {
            method: 'POST',
            headers: hdrs,
            body: fd
        });
        loadAdminLotteries();
    } catch(e) { console.error(e); }
}

// Escaping function to prevent XSS
function escapeHTML(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// --- TON DEPOSIT ---
async function depositTON() {
    if (!tonConnectUI || !tonConnectUI.connected) {
        tg.showAlert("Please connect your TON wallet first using the top bar button.");
        return;
    }

    const amtInput = document.getElementById('deposit-amount').value;
    const amountTon = parseFloat(amtInput);
    if (!amountTon || amountTon <= 0) {
        tg.showAlert("Enter a valid TON amount.");
        return;
    }

    const amountNano = (amountTon * 1e9).toString();
    const adminAddress = "UQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJKZ"; // Replace with real admin address

    const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 360,
        messages: [
            {
                address: adminAddress,
                amount: amountNano,
                // payload: ... (Optional memo or payload)
            }
        ]
    };

    try {
        const result = await tonConnectUI.sendTransaction(transaction);
        // In a real scenario, you'd send the BOC to the backend to verify the transaction

        // Simulating backend verification:
        const res = await fetch('/api/deposit/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ amount_ton: amountTon, boc: result.boc })
        });
        const data = await res.json();

        if (data.success) {
            currentUser.stars_balance = data.new_stars;
            currentUser.ton_balance = data.new_ton;
            updateUI();
            tg.showAlert(`Successfully deposited ${amountTon} TON and received ${data.credited_stars} Stars!`);
        } else {
            tg.showAlert("Error verifying deposit: " + data.error);
        }
    } catch (e) {
        console.error("Transaction failed or rejected", e);
        tg.showAlert("Transaction was cancelled or failed.");
    }
}

// --- LEADERBOARD ---
async function loadLeaderboard() {
    const list = document.getElementById('leaderboard-list');
    if (!list) return;

    list.innerHTML = "Loading...";
    try {
        const res = await fetch('/api/leaderboard/', { headers: getAuthHeaders() });
        const data = await res.json();

        list.innerHTML = '';
        data.leaderboard.forEach((u, i) => {
            let rankColor = "#aaa";
            if(i === 0) rankColor = "gold";
            else if(i === 1) rankColor = "silver";
            else if(i === 2) rankColor = "#cd7f32"; // bronze

            list.innerHTML += `
                <div class="card" style="margin-bottom: 10px; display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap: 10px;">
                        <b style="color:${rankColor}; font-size:1.2em;">#${i+1}</b>
                        <span>${escapeHTML(u.name)}</span>
                    </div>
                    <span style="color:var(--accent); font-weight:bold;">${u.stars} ⭐</span>
                </div>
            `;
        });
    } catch (e) {
        console.error("Failed to load leaderboard", e);
    }
}
