import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update State
state_regex = r'(let state = \{[\s\S]*?cart:.*?,[\s\S]*?products:.*?,)([\s\S]*?isAdmin:.*?,[\s\S]*?user:.*?,[\s\S]*?chats:.*?)(\};)'
def state_repl(m):
    return m.group(1) + '\n                orders: [],\n                reviews: {},\n' + m.group(2) + m.group(3)
content = re.sub(state_regex, state_repl, content)

# 2. Add global sync to initFirestoreSync
sync_func = '''
        async function syncGlobalState() {
            try {
                await window.firebaseSetDoc(window.firebaseDoc(window.firebaseDB, "global", "state"), {
                    orders: state.orders,
                    chats: state.chats,
                    reviews: state.reviews
                });
            } catch(e) { console.error("Sync Error:", e); }
        }
'''
content = content.replace('function initFirestoreSync() {', sync_func + '\n        function initFirestoreSync() {')

# 3. Add Global State listener to initFirestoreSync
listener = '''
            window.firebaseOnSnapshot(window.firebaseDoc(window.firebaseDB, "global", "state"), (doc) => {
                if (doc.exists()) {
                    const data = doc.data();
                    state.orders = data.orders || [];
                    state.chats = data.chats || [];
                    state.reviews = data.reviews || {};
                    
                    if (document.getElementById('view-orders') && !document.getElementById('view-orders').classList.contains('hidden')) renderOrders();
                    if (document.getElementById('view-admin') && !document.getElementById('view-admin').classList.contains('hidden')) renderAdminChats();
                    if (document.getElementById('userChatWindow') && !document.getElementById('userChatWindow').classList.contains('hidden')) renderUserChat();
                    if (window.currentProductId) renderReviews(window.currentProductId);
                }
            });
'''
content = content.replace('}, (error) => {\n                console.error("Error sincronizando Firebase: ", error);\n            });\n        }', '}, (error) => {\n                console.error("Error sincronizando Firebase: ", error);\n            });\n' + listener + '\n        }')

# 4. Replace localStorage calls
# Orders
content = content.replace("const orders = JSON.parse(localStorage.getItem('sercom_orders') || '[]');", "const orders = state.orders;")
content = content.replace("localStorage.setItem('sercom_orders', JSON.stringify(orders));", "syncGlobalState();")

content = content.replace("const allOrders = JSON.parse(localStorage.getItem('sercom_orders') || '[]');", "const allOrders = state.orders;")

# Reviews
content = content.replace("const reviewsMap = JSON.parse(localStorage.getItem('sercom_reviews')) || {};", "const reviewsMap = state.reviews;")
content = content.replace("localStorage.setItem('sercom_reviews', JSON.stringify(reviewsMap));", "syncGlobalState();")

# Chats
content = content.replace("JSON.parse(localStorage.getItem('sercom_chats_v2')) || []", "[]")
content = content.replace("localStorage.setItem('sercom_chats_v2', JSON.stringify(state.chats));", "syncGlobalState();")

# Save back
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Rewrite complete!')
