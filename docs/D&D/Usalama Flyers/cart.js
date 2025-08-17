// cart.js - D&D Shopping Cart for Usalama Flyers
// Stores cart in LocalStorage, renders cart summary, and provides add/remove functions.

const CART_KEY = 'dnd_cart';

function getCart() {
    try {
        return JSON.parse(localStorage.getItem(CART_KEY)) || [];
    } catch {
        return [];
    }
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function addToCart(item) {
    const cart = getCart();
    cart.push(item);
    saveCart(cart);
    renderCartSummary();
}

function removeFromCart(index) {
    const cart = getCart();
    cart.splice(index, 1);
    saveCart(cart);
    renderCartSummary();
}

function getTotal() {
    return getCart().reduce((sum, item) => sum + (item.price || 0), 0);
}

function renderCartSummary() {
    const cart = getCart();
    const cartDiv = document.getElementById('cart-summary');
    if (!cartDiv) return;
    if (cart.length === 0) {
        cartDiv.innerHTML = '<b>Your cart is empty.</b>';
        return;
    }
    // Group items by name/shop/price
    const grouped = {};
    cart.forEach(item => {
        const key = item.name + '|' + item.shop + '|' + item.price;
        if (!grouped[key]) grouped[key] = { ...item, qty: 0 };
        grouped[key].qty++;
    });
    let html = '<b>Your Cart:</b>';
    html += '<table style="width:100%;border-collapse:collapse;margin-top:0.5em;">';
    html += '<thead><tr><th style="text-align:left;padding:0.3em 0.5em;">Item</th><th style="text-align:left;padding:0.3em 0.5em;">Shop</th><th style="text-align:right;padding:0.3em 0.5em;">Price</th><th style="text-align:right;padding:0.3em 0.5em;">Qty</th><th style="text-align:right;padding:0.3em 0.5em;">Subtotal</th><th></th></tr></thead>';
    html += '<tbody>';
    let total = 0;
    let idx = 0;
    Object.values(grouped).forEach(item => {
        const subtotal = item.price * item.qty;
        total += subtotal;
        html += `<tr>` +
            `<td>${item.name}</td>` +
            `<td style='color:#888;'>${item.shop}</td>` +
            `<td style='text-align:right;'>${item.price}gp</td>` +
            `<td style='text-align:right;'>${item.qty}</td>` +
            `<td style='text-align:right;'><b>${subtotal}gp</b></td>` +
            `<td><button onclick="removeFromCart(${idx})" style='margin-left:0.5em;'>Remove</button></td>` +
            `</tr>`;
        idx += item.qty;
    });
    html += '</tbody>';
    html += `<tfoot><tr><td colspan="4" style="text-align:right;"><b>Total:</b></td><td style="text-align:right;"><b>${total}gp</b></td><td></td></tr></tfoot>`;
    html += '</table>';
    cartDiv.innerHTML = html;
}

function setupCartSummary() {
    document.addEventListener('DOMContentLoaded', renderCartSummary);
}

function addNToCart(name, price, shop, qtyId) {
    const qty = parseInt(document.getElementById(qtyId).value, 10);
    if (!qty || qty < 1) return;
    for (let i = 0; i < qty; ++i) {
        addToCart({name, price, shop});
    }
    document.getElementById(qtyId).value = 0;
}

function getCartQuantity(name, shop) {
    console.log("Getting cart quantity for", name, shop);
    return getCart().filter(item => item.name === name && item.shop === shop).length;
}

function updateAllItemQuantities(items) {
    items.forEach(({name, shop, inputId}) => {
        const input = document.getElementById(inputId);
        if (input) {
            input.value = getCartQuantity(name, shop);
        }
    });
}

function setCartQuantity(name, price, shop, newQty) {
    let cart = getCart();
    // Remove all items with this name/shop
    cart = cart.filter(item => !(item.name === name && item.shop === shop));
    // Add newQty items
    for (let i = 0; i < newQty; ++i) {
        cart.push({name, price, shop});
    }
    saveCart(cart);
    renderCartSummary();
}

function setupCartInputs() {
    console.log("Setting up cart inputs");
    document.querySelectorAll('input[data-cart-name][data-cart-price][data-cart-shop]').forEach(input => {
        console.log("Found cart input:", input);
        const name = input.getAttribute('data-cart-name');
        const price = parseFloat(input.getAttribute('data-cart-price'));
        const shop = input.getAttribute('data-cart-shop');
        // Set initial value to current cart quantity
        input.value = getCartQuantity(name, shop);
        // Find the next sibling button with class 'add-to-cart-btn'
        const btn = input.parentElement.querySelector('.add-to-cart-btn');
        if (btn) {
            btn.onclick = function() {
                const qty = parseInt(input.value, 10) || 0;
                setCartQuantity(name, price, shop, qty);
                input.value = getCartQuantity(name, shop);
            };
        }
    });
}

document.addEventListener('DOMContentLoaded', setupCartInputs);

// For flyers: call addToCart({name, price, shop}) on button click.
// Example: <button onclick="addToCart({name: 'Healing Potion', price: 50, shop: 'The Forager\'s Basket'})">Add to Cart</button>

setupCartSummary();
setupCartInputs();