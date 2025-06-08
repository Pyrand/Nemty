
document.getElementById("register-form").onsubmit = async function(e) {
        e.preventDefault();
        const username = document.getElementById("register-username").value.trim();
        const email = document.getElementById("register-email").value.trim();
        const phone = document.getElementById("register-phone").value;
        const password = document.getElementById("register-password").value;

        try {
            const res = await fetch("/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, phone, password })
            });
            const data = await res.json();

            msgBox.textContent = data.message;
            if (data.success) {
                document.getElementById("login-username").value = "";
                document.getElementById("login-password").value = "";
                document.getElementById("login-message").textContent = "";
                document.getElementById("register-username").value = "";
                document.getElementById("register-email").value = "";
                document.getElementById("register-phone").value = "";
                document.getElementById("register-password").value = "";
                document.getElementById("login-tab").classList.add("active");
                document.getElementById("register-tab").classList.remove("active");
                document.getElementById("register-form").style.display = "none";
                document.getElementById("login-form").style.display = "";
            }
        } catch (error) {
            msgBox.textContent = "Could not connect to the server! Please try again.";
        } finally {
            submitBtn.disabled = false;
            submitBtn.classList.remove('button-loading');
        }
    };