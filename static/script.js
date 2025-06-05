document.addEventListener("DOMContentLoaded", function() {
    // SPA initial state: hide main app if not logged in
    checkLogin();

    // Tab switching
    document.getElementById("login-tab").onclick = function() {
        this.classList.add("active");
        document.getElementById("register-tab").classList.remove("active");
        document.getElementById("login-form").style.display = "";
        document.getElementById("register-form").style.display = "none";
    };
    document.getElementById("register-tab").onclick = function() {
        this.classList.add("active");
        document.getElementById("login-tab").classList.remove("active");
        document.getElementById("login-form").style.display = "none";
        document.getElementById("register-form").style.display = "";
    };

    // Login form
    document.getElementById("login-form").onsubmit = async function(e) {
        e.preventDefault();
        const username = document.getElementById("login-username").value;
        const password = document.getElementById("login-password").value;
        const msgBox = document.getElementById("login-message");
        const submitBtn = this.querySelector('button[type="submit"]');

        submitBtn.disabled = true;
        submitBtn.classList.add('button-loading');
        msgBox.textContent = "";

        try {
            const res = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();

            msgBox.textContent = data.message;
            if (data.success) {
                document.getElementById("login-username").value = "";
                document.getElementById("login-password").value = "";
                document.getElementById("login-message").textContent = "";
                document.getElementById("register-username").value = "";
                document.getElementById("register-password").value = "";
                document.getElementById("register-message").textContent = "";
                showApp();
            }
        } catch (error) {
            msgBox.textContent = "Could not connect to the server! Please try again.";
        } finally {
            submitBtn.disabled = false;
            submitBtn.classList.remove('button-loading');
        }

        // Textarea auto-height setup
        const messageTextarea = document.getElementById('message');
        if (messageTextarea) {
            const initialMinHeight = getComputedStyle(messageTextarea).minHeight;

            const adjustTextareaHeight = () => {
                messageTextarea.style.height = 'auto';
                let newHeight = messageTextarea.scrollHeight;
                messageTextarea.style.height = newHeight + 'px';
            };

            messageTextarea.addEventListener('input', adjustTextareaHeight);
            messageTextarea.style.height = initialMinHeight;
        }
    };

    // Register form
    document.getElementById("register-form").onsubmit = async function(e) {
        e.preventDefault();
        const username = document.getElementById("register-username").value.trim();
        const email = document.getElementById("register-email").value.trim();
        const phone = document.getElementById("register-phone").value;
        const password = document.getElementById("register-password").value;
        const msgBox = document.getElementById("register-message");
        const submitBtn = this.querySelector('button[type="submit"]');

        // Validation
        if (username.length < 3) {
            msgBox.textContent = "Username must be at least 3 characters!";
            return;
        }
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
            msgBox.textContent = "Please enter a valid email address!";
            return;
        }
        if (password.length < 6) {
            msgBox.textContent = "Password must be at least 6 characters!";
            return;
        }

        submitBtn.disabled = true;
        submitBtn.classList.add('button-loading');
        msgBox.textContent = "";

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
            }
        } catch (error) {
            msgBox.textContent = "Could not connect to the server! Please try again.";
        } finally {
            submitBtn.disabled = false;
            submitBtn.classList.remove('button-loading');
        }
    };

    // Logout button (in header)
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.onclick = async function() {
            await fetch("/api/logout", { method: "POST" });
            document.getElementById("main-app-area").style.display = "none";
            document.getElementById("auth-area").style.display = "";
            document.querySelector(".chat-box").innerHTML = "";
        };
    }

    

});

function showApp() {
    document.getElementById("auth-area").style.display = "none";
    document.getElementById("main-app-area").style.display = "";

    fetch("/api/check-login")
        .then(res => res.json())
        .then(data => {
            const welcomeDiv = document.getElementById("welcome-user");
            if (data.logged_in && data.user) {
                welcomeDiv.textContent = `Welcome, ${data.user}!`;

                // 🟢 LOAD USER CHAT HISTORY ON LOGIN
                fetch("/api/history")
                    .then(res => res.json())
                    .then(data => {
                        const chatBox = document.querySelector(".chat-box");
                        chatBox.innerHTML = "";

                        document.getElementById("flight-results").innerHTML = "";
                        const hotelResults = document.getElementById("hotel-results");
                        if (hotelResults) hotelResults.innerHTML = "";

                        if (data.history && data.history.length > 0) {
                            data.history.forEach(msg => {
                                if (msg.role === "user" || msg.role === "assistant") {
                                    addMessageToChat(msg.role, msg.content);
                                }
                            });
                        }

                        // YENİ: Flight ve Hotel sonuçlarını doldur
                        if (data.flights && data.flights.length > 0) {
                            showFlights(data.flights);
                        }
                        if (data.hotels && data.hotels.length > 0) {
                            showHotelsStatic(data.hotels);
                        }
                    });
            } else {
                welcomeDiv.textContent = "";
            }
        });
}

function showHotelsStatic(hotels) {
    const box = document.getElementById("hotel-results");
    if (!box) return;
    box.innerHTML = "";

    if (!hotels || hotels.length === 0) {
        box.textContent = "No hotels found.";
        return;
    }

    const ul = document.createElement("ul");
    hotels.forEach(hotel => {
        const li = document.createElement("li");
        li.textContent = hotel;
        ul.appendChild(li);
    });
    box.appendChild(ul);
}


function checkLogin() {
    fetch("/api/check-login")
        .then(res => res.json())
        .then(data => {
            if (data.logged_in) {
                showApp();
            } else {
                document.getElementById("auth-area").style.display = "";
                document.getElementById("main-app-area").style.display = "none";
            }
        });
}

async function sendMessage(event) {
    event.preventDefault();
    const input = document.querySelector("#message");
    const message = input.value.trim();
    if (message === "") return;

    // Find the submit button
    const submitBtn = event.target.querySelector('button[type="submit"]');

    // Disable button and textarea, start loading
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add('button-loading');
    }
    input.disabled = true;

    addMessageToChat("user", message);
    input.value = "";
    if (input.tagName.toLowerCase() === 'textarea') {
        input.style.height = getComputedStyle(input).minHeight;
    }

    const chatBox = document.querySelector(".chat-box");
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "ai";
    loadingMsg.id = "loading-message";
    loadingMsg.innerHTML = `<span style="font-weight: 500; font-size: .96em;">🤖 Nemty</span><br><em>Thinking...</em>`;
    chatBox.appendChild(loadingMsg);

    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        loadingMsg.remove();
        addMessageToChat("ai", data.response);

        if (data.flights && data.flights.length > 0) {
            showFlights(data.flights);
            let cityName = extractCityFromMessage(message, data.response);
            if (cityName) {
                await showHotels(cityName);
            }
        }
    } catch (error) {
        loadingMsg.innerHTML = `<span style="font-weight: 500; font-size: .96em;">🤖 Nemty</span><br><em>An error occurred!</em>`;
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('button-loading');
        }
        input.disabled = false;
    }
}

// Helper: extract city name from user message or AI response
function extractCityFromMessage(userMessage, aiResponse) {
    // Try to find city name in user message first
    const cityPatterns = [
        // Turkish patterns
        /(\w+)(?:'?(?:ye|ya|de|da|den|dan|e|a)\s|'?(?:ye|ya|de|da|den|dan|e|a)$)/gi,
        // English patterns
        /(?:to|in|from|visit)\s+(\w+)/gi,
        // Words starting with capital letter (city names)
        /\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g
    ];

    let cities = [];

    // Extract city names from user message
    cityPatterns.forEach(pattern => {
        const matches = userMessage.match(pattern);
        if (matches) {
            matches.forEach(match => {
                let city = match.replace(/(?:'?(?:ye|ya|de|da|den|dan|e|a)\s*|to|in|from|visit)/gi, '').trim();
                if (city.length > 2) {
                    cities.push(city);
                }
            });
        }
    });

    // Extract city names from AI response
    const aiCityMatches = aiResponse.match(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g);
    if (aiCityMatches) {
        cities.push(...aiCityMatches.filter(city => city.length > 2));
    }

    // Return most common city
    if (cities.length > 0) {
        const cityCount = {};
        cities.forEach(city => {
            const cleanCity = city.toLowerCase();
            cityCount[cleanCity] = (cityCount[cleanCity] || 0) + 1;
        });

        let mostFrequentCity = '';
        let maxCount = 0;
        for (const [city, count] of Object.entries(cityCount)) {
            if (count > maxCount) {
                maxCount = count;
                mostFrequentCity = city;
            }
        }

        return mostFrequentCity.charAt(0).toUpperCase() + mostFrequentCity.slice(1);
    }

    return null;
}

function addMessageToChat(role, content) {
    const chatBox = document.querySelector(".chat-box");
    const msg = document.createElement("div");
    msg.className = role === "user" ? "user" : "ai";

    let label = "";
    if (role === "ai") {
        label = `<span style="font-weight: 500; font-size: .96em;">🤖 Nemty</span><br>`;
    } else {
        label = "";
    }

    // No label for user, "🤖 Nemty" at the top for bot
    msg.innerHTML = `${label}${marked.parse(content).replace(/^<p>|<\/p>$/g, '')}`;

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function resetChat() {
    await fetch("/reset");
    document.querySelector(".chat-box").innerHTML = "";
    // Also clear flight and hotel results
    document.getElementById("flight-results").innerHTML = "";
    const hotelResults = document.getElementById("hotel-results");
    if (hotelResults) hotelResults.innerHTML = "";
}

async function showFlights(flights) {
    const flightInfoMsg = addInfoMessage("flight");
    const flightBox = document.getElementById("flight-results");
    flightBox.innerHTML = "";

    if (flightInfoMsg) flightInfoMsg.remove();

    if (!flights || flights.length === 0) {
        flightBox.textContent = "No flights found.";
        return;
    }

    const ul = document.createElement("ul");
    flights.forEach(flight => {
        const li = document.createElement("li");
        li.textContent = flight;
        ul.appendChild(li);
    });
    flightBox.appendChild(ul);
}

async function showHotels(city) {
    const hotelInfoMsg = addInfoMessage("hotel");

    try {
        const res = await fetch("/hotels", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ city: city, message: message })
        });

        const data = await res.json();
        const box = document.getElementById("hotel-results");
        if (!box) return;

        box.innerHTML = "";

        if (!data.hotels || data.hotels.length === 0) {
            box.textContent = "No hotels found.";
            return;
        }

        const ul = document.createElement("ul");
        data.hotels.forEach(hotel => {
            const li = document.createElement("li");
            li.textContent = hotel;
            ul.appendChild(li);
        });
        box.appendChild(ul);
    } catch (error) {
        const box = document.getElementById("hotel-results");
        if (box) box.textContent = "An error occurred while searching for hotels!";
    } finally {
        if (hotelInfoMsg) hotelInfoMsg.remove();
    }
}

// Password show/hide toggle
document.querySelectorAll(".toggle-password").forEach(function(btn) {
    btn.addEventListener("click", function() {
        const input = this.parentElement.querySelector("input");
        if (input.type === "password") {
            input.type = "text";
            this.style.color = "#007BFF";
        } else {
            input.type = "password";
            this.style.color = "#888";
        }
    });
});

function addInfoMessage(type) {
    const chatBox = document.querySelector(".chat-box");
    const msg = document.createElement("div");
    msg.className = "ai";

    let text = "";
    if (type === "flight") text = "<em>Searching for flights...</em>";
    else if (type === "hotel") text = "<em>Searching for hotels...</em>";
    else text = "<em>Thinking...</em>";

    msg.innerHTML = `<span style="font-weight: 500; font-size: .96em;">🤖 Nemty</span><br>${text}`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msg;
}


function showSection(section, btn) {
      document.querySelectorAll('.section-content').forEach(div => div.style.display = 'none');
      document.getElementById('section-' + section).style.display = '';

      // Navigation'da aktif buton vurgusu
      if (btn) {
        document.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }
    }
    // Otomatik olarak Home'u aç (JS yüklenince)
    document.addEventListener("DOMContentLoaded", function() {
      showSection('home', document.querySelector('.nav-link'));
    });