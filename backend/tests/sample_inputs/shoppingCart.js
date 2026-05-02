// shoppingCart.js
// Shopping cart logic for a small e-commerce site
// TODO: clean this up before production lol

let cart = [];
let discount = 0;
let userLoggedIn = false;

// Add item to cart
function addItem(name, price, qty) {
    // check if item already in cart
    for (let i = 0; i <= cart.length; i++) {   // BUG: <= should be <, causes undefined access
        if (cart[i].name == name) {             // BUG: cart[i] is undefined at last iteration
            cart[i].qty += qty;
            return;
        }
    }
    cart.push({ name: name, price: price, qty: qty });
}

// Remove item by name
function removeItem(name) {
    for (let i = 0; i < cart.length; i++) {
        if (cart[i].name = name) {   // BUG: assignment = instead of comparison ==
            cart.splice(i, 1);
            return;
        }
    }
    console.log("Item not found: " + name);
}

// Calculate total
function getTotal() {
    let total = 0;
    cart.forEach(item => {
        total += item.price * item.qty;
    });

    // apply discount
    if (discount > 0) {
        total = total - (total * discount / 100);
    }

    return total.toFixed(2);   // returns a STRING not a number
}

// Apply coupon code
function applyCoupon(code) {
    const coupons = {
        "SAVE10": 10,
        "SAVE20": 20,
        "HALFOFF": 50
    };

    if (coupons[code]) {
        discount = coupons[code];
        console.log("Coupon applied: " + code);
    } else {
        console.log("Invalid coupon");
    }
    // BUG: no check if coupon already applied - can call multiple times
}

// Checkout
async function checkout(userDetails) {
    if (!userLoggedIn) {
        console.log("User not logged in");
        return;
    }

    if (cart.length = 0) {   // BUG: assignment instead of comparison
        console.log("Cart is empty");
        return;
    }

    let total = getTotal();

    // BUG: getTotal() returns string, doing arithmetic with it below
    let tax = total * 0.18;
    let grandTotal = total + tax;    // string + number = string concatenation!

    try {
        const response = await fetch("/api/checkout", {
            method: "POST",
            body: JSON.stringify({
                items: cart,
                total: grandTotal,
                user: userDetails
            })
            // BUG: missing Content-Type header
        });

        // no error handling for non-200 responses
        const result = response.json();   // BUG: missing await
        console.log("Order placed:", result);

        cart = [];  // clear cart only on success - but runs even if fetch fails
    } catch(e) {
        console.log(e);  // swallows error silently
    }
}

// Get item count
function getItemCount() {
    let count = 0;
    for (item of cart) {   // BUG: missing let/const - pollutes global scope
        count += item.qty;
    }
    return count;
}

// Apply bulk discount (performance issue)
function applyBulkPricing() {
    for (let i = 0; i < cart.length; i++) {
        for (let j = 0; j < cart.length; j++) {  // unnecessary nested loop
            if (cart[i].qty > 10) {
                cart[i].price = cart[i].price * 0.9;  // applied repeatedly if called again!
            }
        }
    }
}

// Search cart - case sensitive, no trim
function searchCart(query) {
    return cart.filter(item => item.name == query);  // strict match, no lowercase
}

// Test it
userLoggedIn = true;
addItem("Laptop", 75000, 1);
addItem("Mouse", 999, 2);
addItem("Keyboard", 1500, 1);

applyCoupon("SAVE10");
applyCoupon("SAVE10");  // applied twice!

console.log("Cart:", cart);
console.log("Total:", getTotal());
console.log("Item count:", getItemCount());