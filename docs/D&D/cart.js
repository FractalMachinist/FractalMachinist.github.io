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
    let html = '<b>Your Cart:</b><ul style="list-style:none;padding:0;">';
    cart.forEach((item, idx) => {
        html += `<li style='margin-bottom:0.5em;'>${item.name} <span style='color:#888;'>(${item.shop})</span> - <b>${item.price}gp</b> <button onclick="removeFromCart(${idx})" style='margin-left:0.5em;'>Remove</button></li>`;
    });
    html += '</ul>';
    html += `<div style='margin-top:0.5em;'><b>Total: ${getTotal()}gp</b></div>`;
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