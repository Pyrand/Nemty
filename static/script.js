async function sendMessage(event) {
    event.preventDefault();
    const input = document.querySelector("#message");
    const message = input.value.trim();
    if (message === "") return;
  
    addMessageToChat("user", message);
    input.value = "";
  
    const chatBox = document.querySelector(".chat-box");
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "ai";
    loadingMsg.id = "loading-message";
    loadingMsg.innerHTML = "🤖 <br><em>Thinking...</em>";
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
      console.log("Chat response data:", data); // Debug log
      
      // loading mesajını kaldır
      loadingMsg.remove();
  
      addMessageToChat("ai", data.response);

      // Uçuş sonuçlarını göster
      if (data.flights && data.flights.length > 0) {
        showFlights(data.flights);
        
        // Uçuş verisi varsa, şehir adını AI yanıtından veya mesajdan çıkarmaya çalış
        let cityName = extractCityFromMessage(message, data.response);
        console.log("Extracted city name:", cityName); // Debug log
        
        if (cityName) {
          console.log("Calling showHotels with:", cityName); // Debug log
          await showHotels(cityName);
        } else {
          console.log("No city name extracted for hotels"); // Debug log
        }
      }

    } catch (error) {
      console.error("Error in sendMessage:", error);
      loadingMsg.innerHTML = "🤖 <br><em>Bir hata oluştu!</em>";
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
  
    // Emojili, Markdown uyumlu içerik
    const emoji = role === "user" ? "🧍" : "🤖";
    msg.innerHTML = `${emoji} <br>${marked.parse(content).replace(/^<p>|<\/p>$/g, '')}`;
  
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
    const flightBox = document.getElementById("flight-results");
    flightBox.innerHTML = "";

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
    console.log(`[DEBUG] showHotels called with city: ${city}`); // Debug log
    
    try {
      const res = await fetch("/hotels", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city: city, message: message })
      });
      
      console.log(`[DEBUG] Hotels API response status: ${res.status}`); // Debug log
      
      const data = await res.json();
      console.log("[DEBUG] Hotels API response data:", data); // Debug log

      const box = document.getElementById("hotel-results");
      if (!box) {
        console.error("[DEBUG] hotel-results element not found!");
        return;
      }
      
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
      
      console.log("[DEBUG] Hotels displayed successfully"); // Debug log
      
    } catch (error) {
      console.error("[DEBUG] Error in showHotels:", error);
    }
  }