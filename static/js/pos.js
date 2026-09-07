/* =========================================================
   FASTFOOD EXPRESS - POS JAVASCRIPT LOGIC
   ========================================================= */

let cart = [];
const IVA_RATE = 0.15; // 15% IVA Ecuador

document.addEventListener('DOMContentLoaded', () => {
    initCategoryFilter();
    initSearchFilter();
    initPaymentListeners();
    initCheckoutForm();
});

// 1. Filtrado por categorías
function initCategoryFilter() {
    const tabs = document.querySelectorAll('.category-tab-btn');
    const items = document.querySelectorAll('.pos-item-card');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const categoryId = tab.dataset.category;
            items.forEach(item => {
                if (categoryId === 'all' || item.dataset.category === categoryId) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
}

// 2. Búsqueda rápida de productos
function initSearchFilter() {
    const searchInput = document.getElementById('posSearchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const items = document.querySelectorAll('.pos-item-card');

        items.forEach(item => {
            const name = item.dataset.name.toLowerCase();
            const code = (item.dataset.code || '').toLowerCase();
            if (name.includes(query) || code.includes(query)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });
}

// 3. Agregar producto al carrito
function addToCart(id, name, price, maxStock, emoji) {
    if (maxStock <= 0) {
        showToast('Producto agotado', 'No hay stock disponible para este producto.', 'error');
        return;
    }

    const existingIndex = cart.findIndex(item => item.id === id);

    if (existingIndex > -1) {
        if (cart[existingIndex].cantidad + 1 > maxStock) {
            showToast('Stock máximo alcanzado', `Solo hay ${maxStock} unidades disponibles en inventario.`, 'warning');
            return;
        }
        cart[existingIndex].cantidad += 1;
    } else {
        cart.push({
            id: id,
            name: name,
            price: parseFloat(price),
            cantidad: 1,
            maxStock: parseInt(maxStock),
            emoji: emoji
        });
    }

    renderCart();
}

// 4. Modificar cantidad
function updateQuantity(id, delta) {
    const index = cart.findIndex(item => item.id === id);
    if (index === -1) return;

    const newQty = cart[index].cantidad + delta;

    if (newQty <= 0) {
        cart.splice(index, 1);
    } else if (newQty > cart[index].maxStock) {
        showToast('Stock insuficiente', `No puedes agregar más de ${cart[index].maxStock} unidades.`, 'warning');
        return;
    } else {
        cart[index].cantidad = newQty;
    }

    renderCart();
}

// 5. Vaciar carrito
function clearCart() {
    if (cart.length === 0) return;
    if (confirm('¿Desea vaciar el carrito de venta?')) {
        cart = [];
        renderCart();
    }
}

// 6. Renderizar carrito y totales
function renderCart() {
    const container = document.getElementById('cartItemsList');
    const subtotalEl = document.getElementById('cartSubtotal');
    const ivaEl = document.getElementById('cartIva');
    const totalEl = document.getElementById('cartTotal');
    const btnCheckout = document.getElementById('btnProcessCheckout');
    const countBadge = document.getElementById('cartCountBadge');

    if (!container) return;

    if (cart.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: var(--text-dim); padding: 40px 10px;">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">🛒</div>
                <p style="font-weight: 500;">El carrito está vacío</p>
                <small>Seleccione productos del menú para iniciar una orden</small>
            </div>
        `;
        if (subtotalEl) subtotalEl.innerText = '$0.00';
        if (ivaEl) ivaEl.innerText = '$0.00';
        if (totalEl) totalEl.innerText = '$0.00';
        if (btnCheckout) btnCheckout.disabled = true;
        if (countBadge) countBadge.innerText = '0';
        calculateChange(0);
        return;
    }

    let total = 0;
    let totalItems = 0;
    let html = '';

    cart.forEach(item => {
        const itemTotal = item.price * item.cantidad;
        total += itemTotal;
        totalItems += item.cantidad;

        html += `
            <div class="cart-item">
                <div style="font-size: 1.4rem;">${item.emoji || '🍔'}</div>
                <div class="cart-item-info">
                    <div class="cart-item-title">${item.name}</div>
                    <div class="cart-item-unit-price">$${item.price.toFixed(2)} c/u</div>
                </div>
                <div class="cart-qty-ctrl">
                    <button type="button" class="qty-btn" onclick="updateQuantity(${item.id}, -1)">-</button>
                    <span class="qty-val">${item.cantidad}</span>
                    <button type="button" class="qty-btn" onclick="updateQuantity(${item.id}, 1)">+</button>
                </div>
                <div class="cart-item-subtotal">$${itemTotal.toFixed(2)}</div>
            </div>
        `;
    });

    // Desglose: El precio del menú es PVP (IVA 15% incluido)
    const subtotal = total / (1 + IVA_RATE);
    const iva = total - subtotal;

    container.innerHTML = html;
    if (subtotalEl) subtotalEl.innerText = `$${subtotal.toFixed(2)}`;
    if (ivaEl) ivaEl.innerText = `$${iva.toFixed(2)}`;
    if (totalEl) totalEl.innerText = `$${total.toFixed(2)}`;
    if (btnCheckout) btnCheckout.disabled = false;
    if (countBadge) countBadge.innerText = totalItems;

    calculateChange(total);
}

// 7. Cálculo de cambio y soporte de billetes rápidos
function initPaymentListeners() {
    const cashInput = document.getElementById('cashReceivedInput');
    const paymentMethodSelect = document.getElementById('paymentMethodSelect');
    const cashContainer = document.getElementById('cashContainer');

    if (paymentMethodSelect) {
        paymentMethodSelect.addEventListener('change', (e) => {
            if (cashContainer) {
                cashContainer.style.display = e.target.value === 'EFECTIVO' ? 'block' : 'none';
            }
        });
    }

    if (cashInput) {
        cashInput.addEventListener('input', () => {
            const total = getCurrentTotal();
            calculateChange(total);
        });
    }
}

function setQuickCash(amount) {
    const cashInput = document.getElementById('cashReceivedInput');
    if (!cashInput) return;

    if (amount === 'exact') {
        const total = getCurrentTotal();
        cashInput.value = total.toFixed(2);
    } else {
        cashInput.value = parseFloat(amount).toFixed(2);
    }
    const total = getCurrentTotal();
    calculateChange(total);
}

function getCurrentTotal() {
    return cart.reduce((acc, item) => acc + (item.price * item.cantidad), 0);
}

function calculateChange(total) {
    const cashInput = document.getElementById('cashReceivedInput');
    const changeDisplay = document.getElementById('changeDisplay');
    if (!cashInput || !changeDisplay) return;

    const received = parseFloat(cashInput.value) || 0;
    if (received >= total && total > 0) {
        const change = received - total;
        changeDisplay.innerText = `$${change.toFixed(2)}`;
        changeDisplay.style.color = 'var(--success)';
    } else {
        changeDisplay.innerText = '$0.00';
        changeDisplay.style.color = 'var(--text-dim)';
    }
}

// 8. Procesar Venta / Checkout AJAX
function initCheckoutForm() {
    const btnCheckout = document.getElementById('btnProcessCheckout');
    if (!btnCheckout) return;

    btnCheckout.addEventListener('click', async () => {
        if (cart.length === 0) {
            showToast('Carrito vacío', 'Agregue productos antes de cobrar.', 'warning');
            return;
        }

        const total = getCurrentTotal();
        const metodoPago = document.getElementById('paymentMethodSelect').value;
        const cashInput = document.getElementById('cashReceivedInput');
        const montoRecibido = parseFloat(cashInput ? cashInput.value : total) || total;

        if (metodoPago === 'EFECTIVO' && montoRecibido < total) {
            showToast('Monto insuficiente', `El monto recibido ($${montoRecibido.toFixed(2)}) es menor al total ($${total.toFixed(2)}).`, 'error');
            return;
        }

        const payload = {
            cliente_nombre: document.getElementById('customerNameInput').value.trim() || 'Consumidor Final',
            cliente_identificacion: document.getElementById('customerIdInput').value.trim() || '9999999999',
            metodo_pago: metodoPago,
            monto_recibido: montoRecibido,
            observaciones: document.getElementById('orderNotesInput')?.value || '',
            items: cart.map(i => ({ id: i.id, cantidad: i.cantidad }))
        };

        btnCheckout.disabled = true;
        btnCheckout.innerText = 'Procesando Venta...';

        try {
            const csrfToken = getCookie('csrftoken');
            const response = await fetch('/api/pos/procesar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success) {
                showToast('¡Venta Exitosa!', `Ticket #${result.ticket_numero} generado correctamente.`, 'success');
                
                // Actualizar el modal de ticket
                showReceiptModal(result.receipt_url, result.ticket_numero, result.total, result.cambio);
                
                // Limpiar carrito
                cart = [];
                renderCart();
                if (cashInput) cashInput.value = '';
            } else {
                showToast('Error en la venta', result.error || 'Ocurrió un error inesperado.', 'error');
            }
        } catch (error) {
            showToast('Error de conexión', 'No se pudo conectar con el servidor.', 'error');
            console.error(error);
        } finally {
            btnCheckout.disabled = false;
            btnCheckout.innerHTML = '💳 Cobrar y Generar Ticket';
        }
    });
}

// 9. Modal de Recibo
function showReceiptModal(receiptUrl, ticketNum, total, cambio) {
    const modal = document.getElementById('receiptModal');
    const iframe = document.getElementById('receiptIframe');
    if (!modal || !iframe) {
        window.open(receiptUrl, '_blank');
        return;
    }

    iframe.src = receiptUrl;
    modal.style.display = 'flex';
}

function closeReceiptModal() {
    const modal = document.getElementById('receiptModal');
    if (modal) modal.style.display = 'none';
    // Recargar página para actualizar stock visual
    window.location.reload();
}

// 10. Helper Toast & Cookies
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.boxShadow = 'var(--shadow-md)';
    toast.innerHTML = `
        <div style="font-size: 1.2rem;">${type === 'success' ? '✅' : (type === 'error' ? '❌' : '⚠️')}</div>
        <div>
            <strong style="display: block; font-size: 0.9rem;">${title}</strong>
            <span style="font-size: 0.82rem; opacity: 0.9;">${message}</span>
        </div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
