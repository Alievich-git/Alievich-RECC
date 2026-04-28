with open('templates/login.html', 'r') as f:
    content = f.read()

old_forms = """            <form id="loginForm" class="auth-form active" action="/login" method="POST">
                <div class="input-group">
                    <input type="text" name="username" placeholder="Username" required autocomplete="username">
                </div>
                <div class="input-group">
                    <input type="password" name="password" placeholder="Password" required autocomplete="current-password">
                </div>
                <button type="submit" class="primary-btn">Secure Login</button>
            </form>

            <form id="registerForm" class="auth-form" action="/register" method="POST">
                <div class="input-group">
                    <input type="text" name="username" placeholder="Choose a Username" required autocomplete="username">
                </div>
                <div class="input-group">
                    <input type="password" name="password" placeholder="Choose a Password" required autocomplete="new-password">
                </div>
                <button type="submit" class="primary-btn" style="background: rgba(35, 213, 213, 0.2); border: 1px solid var(--primary); color: #fff;">Create Account</button>
            </form>"""

new_forms = """            <form id="loginForm" class="auth-form active" action="/login" method="POST">
                <div class="input-group">
                    <input type="email" name="email" placeholder="Email Address" required autocomplete="email">
                </div>
                <div class="input-group">
                    <input type="password" name="password" placeholder="Password" required autocomplete="current-password">
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; font-size: 0.9rem;">
                    <label style="color: var(--text-muted); display: flex; align-items: center; cursor: pointer;">
                        <input type="checkbox" name="remember" style="margin-right: 8px;"> Remember Me
                    </label>
                    <a href="#" onclick="openForgotModal(); return false;" style="color: var(--primary); text-decoration: none;">Forgot Password?</a>
                </div>
                <button type="submit" class="primary-btn">Secure Login</button>
            </form>

            <form id="registerForm" class="auth-form" action="/register" method="POST">
                <div class="input-group">
                    <input type="email" name="email" placeholder="Email Address" required autocomplete="email">
                </div>
                <div class="input-group">
                    <input type="password" name="password" placeholder="Choose a Password" required autocomplete="new-password">
                </div>
                <button type="submit" class="primary-btn" style="background: rgba(35, 213, 213, 0.2); border: 1px solid var(--primary); color: #fff;">Create Account</button>
            </form>"""
content = content.replace(old_forms, new_forms)

modal_html = """
    <!-- Forgot Password Modal -->
    <div id="forgotModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 100; align-items: center; justify-content: center; backdrop-filter: blur(5px);">
        <div class="glass-panel" style="max-width: 400px; width: 90%; text-align: center; position: relative;">
            <button onclick="closeForgotModal()" style="position: absolute; top: 15px; right: 20px; background: none; border: none; color: #fff; font-size: 1.5rem; cursor: pointer;">&times;</button>
            <h2 style="font-size: 1.5rem; margin-bottom: 10px;">Reset Password</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 20px;">Enter your email to receive a secure reset link.</p>
            <div id="forgotMsg" style="margin-bottom: 15px; font-size: 0.9rem; font-weight: 500;"></div>
            <div class="input-group">
                <input type="email" id="forgotEmail" placeholder="Your Email Address" required>
            </div>
            <button id="forgotBtn" onclick="sendResetLink()" class="primary-btn">Send Reset Link</button>
        </div>
    </div>
"""

content = content.replace("    <script>", modal_html + "\n    <script>")

js_funcs = """        function openForgotModal() {
            document.getElementById('forgotModal').style.display = 'flex';
            document.getElementById('forgotMsg').textContent = '';
            document.getElementById('forgotEmail').value = '';
        }
        function closeForgotModal() {
            document.getElementById('forgotModal').style.display = 'none';
        }
        function sendResetLink() {
            const email = document.getElementById('forgotEmail').value.trim();
            if (!email) return;
            const btn = document.getElementById('forgotBtn');
            const msg = document.getElementById('forgotMsg');
            btn.textContent = 'Sending...';
            btn.disabled = true;
            
            fetch('/forgot_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email })
            }).then(res => res.json()).then(data => {
                btn.textContent = 'Send Reset Link';
                btn.disabled = false;
                if (data.success) {
                    msg.style.color = '#23d5d5';
                    msg.textContent = 'If that email exists, a reset link has been sent.';
                } else {
                    msg.style.color = '#ff5555';
                    msg.textContent = data.message || 'Error sending link.';
                }
            }).catch(err => {
                btn.textContent = 'Send Reset Link';
                btn.disabled = false;
                msg.style.color = '#ff5555';
                msg.textContent = 'Network error.';
            });
        }
"""
content = content.replace("        function switchTab(tab) {", js_funcs + "\n        function switchTab(tab) {")

with open('templates/login.html', 'w') as f:
    f.write(content)

