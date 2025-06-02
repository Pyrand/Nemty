document.addEventListener("DOMContentLoaded", function() {
    // SPA state başlangıcı: eğer giriş yapılmamışsa ana app'ı gizle
    checkLogin();

    // Tab arası geçiş
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

    // Login formu
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
                  msgBox.textContent = "Sunucuya bağlanılamadı! Lütfen tekrar deneyin.";
              } finally {
                  submitBtn.disabled = false;
                  submitBtn.classList.remove('button-loading');
              }

              // Textarea yükseklik ayarı (senin kodunda var diye korudum)
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


    // Register formu
        // Register formu
        document.getElementById("register-form").onsubmit = async function(e) {
          e.preventDefault();
          const username = document.getElementById("register-username").value.trim();
          const email = document.getElementById("register-email").value.trim();
          const phone = document.getElementById("register-phone").value;
          const password = document.getElementById("register-password").value;
          const msgBox = document.getElementById("register-message");
          const submitBtn = this.querySelector('button[type="submit"]');

          // Validation bloğu
          if (username.length < 3) {
              msgBox.textContent = "Kullanıcı adı en az 3 karakter olmalı!";
              return;
          }
          if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
              msgBox.textContent = "Geçerli bir e-posta adresi girin!";
              return;
          }
          if (password.length < 6) {
              msgBox.textContent = "Şifre en az 6 karakter olmalı!";
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
              msgBox.textContent = "Sunucuya bağlanılamadı! Lütfen tekrar deneyin.";
          } finally {
              // Her durumda (başarılı, hatalı, catch çalışsa bile) butonu açar ve animasyonu kaldırır
              submitBtn.disabled = false;
              submitBtn.classList.remove('button-loading');
          }
      };



    // Çıkış yapmak için (header’a ekleyeceğin bir çıkış butonu için)
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

                // 🟢 GİRİŞTE KULLANICI MESAJ GEÇMİŞİNİ YÜKLE
                fetch("/api/history")
                  .then(res => res.json())
                  .then(data => {
                      const chatBox = document.querySelector(".chat-box");
                      chatBox.innerHTML = ""; // Kutuyu temizle
                      if (data.history && data.history.length > 0) {
                          data.history.forEach(msg => {
                              if (msg.role === "user" || msg.role === "assistant") {
                                  addMessageToChat(msg.role, msg.content);
                              }
                });
        }
    });

            } else {
                welcomeDiv.textContent = "";
            }
        });
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

    // Gönder butonunu bul
    const submitBtn = event.target.querySelector('button[type="submit"]');

    // Buton ve textarea'yı disable et, loading başlat
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
        loadingMsg.innerHTML = "🤖 <br><em>Bir hata oluştu!</em>";
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('button-loading');
        }
        input.disabled = false;
    }
}


  // Şehir adını mesajdan veya AI yanıtından çıkaran yardımcı fonksiyon
  function extractCityFromMessage(userMessage, aiResponse) {
    // Önce kullanıcı mesajından şehir adı bulmaya çalış
    const cityPatterns = [
      // Türkçe kalıplar
      /(\w+)(?:'?(?:ye|ya|de|da|den|dan|e|a)\s|'?(?:ye|ya|de|da|den|dan|e|a)$)/gi,
      // İngilizce kalıplar
      /(?:to|in|from|visit)\s+(\w+)/gi,
      // Büyük harfle başlayan kelimeler (şehir isimleri)
      /\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g
    ];

    let cities = [];
    
    // Kullanıcı mesajından şehir adları çıkar
    cityPatterns.forEach(pattern => {
      const matches = userMessage.match(pattern);
      if (matches) {
        matches.forEach(match => {
          // Temizle ve ekle
          let city = match.replace(/(?:'?(?:ye|ya|de|da|den|dan|e|a)\s*|to|in|from|visit)/gi, '').trim();
          if (city.length > 2) {
            cities.push(city);
          }
        });
      }
    });

    // AI yanıtından da şehir adları çıkar
    const aiCityMatches = aiResponse.match(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g);
    if (aiCityMatches) {
      cities.push(...aiCityMatches.filter(city => city.length > 2));
    }

    // En yaygın şehir adını döndür
    if (cities.length > 0) {
      // Frequency count
      const cityCount = {};
      cities.forEach(city => {
        const cleanCity = city.toLowerCase();
        cityCount[cleanCity] = (cityCount[cleanCity] || 0) + 1;
      });
      
      // En sık geçen şehri bul
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

    // Kullanıcıda başlık yok, botta başta "🤖 Nemty" var
    msg.innerHTML = `${label}${marked.parse(content).replace(/^<p>|<\/p>$/g, '')}`;

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

  
  async function resetChat() {
    await fetch("/reset");
    document.querySelector(".chat-box").innerHTML = "";
    // Ayrıca uçuş ve otel kutularını da temizle
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
        flightBox.textContent = "Uçuş bulunamadı.";
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
  
  // --- OTEL GÖSTERME FONKSİYONU (DEBUG LOGLARI EKLENDİ) ---
  async function showHotels(city) {
    // Oteller aranıyor mesajı göster
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
            box.textContent = "Otel bulunamadı.";
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
        // Hata mesajı
        const box = document.getElementById("hotel-results");
        if (box) box.textContent = "Otel arama sırasında bir hata oluştu!";
    } finally {
        // Mesajı kaldır
        if (hotelInfoMsg) hotelInfoMsg.remove();
    }
}


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
    if (type === "flight") text = "<em>Uçuşlar aranıyor...</em>";
    else if (type === "hotel") text = "<em>Oteller aranıyor...</em>";
    else text = "<em>Thinking...</em>";

    msg.innerHTML = `<span style="font-weight: 500; font-size: .96em;">🤖 Nemty</span><br>${text}`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msg;
}
