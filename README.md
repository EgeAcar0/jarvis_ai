# JARVIS AI Assistant

JARVIS AI, Tony Stark'ın yapay zeka asistanından esinlenilmiş, doğal dil işleme ve sistem yönetimi yeteneklerine sahip bir yapay zeka asistanıdır. Kullanıcılar günlük görevlerini gerçekleştirmek, sistemlerini yönetmek ve çeşitli işlemler yapmak için JARVIS ile konuşabilirler.

## Özellikler

- Doğal dil anlama yeteneği
- Sistem komutlarını çalıştırma
- Dosya ve klasör yönetimi
- Sistem kaynaklarını izleme (CPU, bellek, disk kullanımı)
- Uzak sunucu yönetimi (SSH üzerinden)
- Gerçek zamanlı sohbet arayüzü

## Kurulum

### Ön Gereksinimler

- Python 3.9 veya üzeri
- Node.js 16 veya üzeri
- MongoDB (Community Sürümü)

#### MongoDB Kurulumu

1. **Windows için**:
   - [MongoDB Community Server](https://www.mongodb.com/try/download/community) adresinden indirin
   - Kurulum sihirbazını çalıştırın ve varsayılan ayarları kullanın
   - Kurulum sırasında "Install MongoDB as a Service" seçeneğini işaretleyin
   - Kurulum tamamlandıktan sonra MongoDB servisinin çalıştığından emin olun:
     ```
     services.msc
     ```
     (Açılan pencerede "MongoDB" servisinin "Çalışıyor" durumunda olduğunu kontrol edin)

2. **Linux (Ubuntu/Debian) için**:
   ```bash
   # MongoDB için GPG anahtarını ekleyin
   sudo apt-get install gnupg
   curl -fsSL https://pgp.mongodb.com/server-6.0.asc | \
      sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg \
      --dearmor

   # Repository ekleyin
   echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -c -s)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

   # MongoDB'yi yükleyin
   sudo apt-get update
   sudo apt-get install -y mongodb-org

   # MongoDB servisini başlatın
   sudo systemctl start mongod
   sudo systemctl enable mongod
   ```

3. **MacOS için**:
   ```bash
   # Homebrew ile kurulum
   brew tap mongodb/brew
   brew update
   brew install mongodb-community

   # MongoDB servisini başlatın
   brew services start mongodb-community
   ```

4. **MongoDB'yi Doğrulama**:
   Terminal veya Komut İstemi'ni açıp aşağıdaki komutu çalıştırın:
   ```bash
   mongosh
   ```
   Eğer MongoDB kabuğu açılıyorsa, kurulum başarılı demektir. Çıkmak için `exit` yazabilirsiniz.

5. **Veritabanı Kullanıcısı Oluşturma (Opsiyonel)**:
   ```bash
   mongosh
   use admin
   db.createUser({
     user: "adminUser",
     pwd: "sifreniz",
     roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
   })
   exit
   ```
   Daha sonra `backend/.env` dosyanızda bağlantı dizesini güncelleyebilirsiniz:
   ```
   MONGO_URL="mongodb://adminUser:sifreniz@localhost:27017/"
   ```

### Projeyi İndirme ve Kurulum

1. Öncelikle projeyi GitHub'dan klonlayın:
   ```bash
   git clone https://github.com/kullaniciadiniz/jarvis-ai.git
   cd jarvis-ai
   ```

### Backend Kurulumu

1. Sanal ortam oluşturun ve etkinleştirin:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows için
   # veya
   source .venv/bin/activate  # Linux/macOS için
   ```

2. Gerekli Python paketlerini yükleyin:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. `emergentintegrations` klasörünü site-packages'a kopyalayın:
   ```bash
   # Windows için
   xcopy /E /I /Y emergentintegrations "%VIRTUAL_ENV%\Lib\site-packages\emergentintegrations"
   
   # Linux/macOS için
   cp -r emergentintegrations "$VIRTUAL_ENV/lib/python3.9/site-packages/"
   ```

4. Ortam değişkenlerini ayarlayın:
   - `backend` klasöründe `.env` dosyası oluşturun ve gerekli değişkenleri ekleyin:
     ```
     MONGO_URL=mongodb://localhost:27017
     GEMINI_API_KEY=your_gemini_api_key
     ```

### Frontend Kurulumu

1. Gerekli Node.js paketlerini yükleyin:
   ```bash
   cd frontend
   npm install
   ```

## Çalıştırma

1. Backend'i başlatın:
   ```bash
   cd backend
   python server.py
   ```

2. Frontend'i başlatın (yeni bir terminal penceresinde):
   ```bash
   cd frontend
   npm start
   ```

3. Tarayıcınızda `http://localhost:3000` adresini açın.

## Kullanım

1. Web arayüzüne giriş yapın
2. JARVIS ile sohbet etmeye başlayın
3. Örnek komutlar:
   - "Masaüstüme yeni bir klasör oluştur"
   - "Sistem bilgilerini göster"
   - "Bilgisayarımın hafıza kullanımını göster"

## Katkıda Bulunma

1. Bu projeyi fork edin
2. Yeni bir branch oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'inize push işlemi yapın (`git push origin yeni-ozellik`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Projenize MIT lisansı eklemek için aşağıdaki adımları izleyin:

1. Projenizin kök dizininde `LICENSE` adında yeni bir dosya oluşturun
2. Aşağıdaki metni kopyalayıp yapıştırın (yıl ve telif hakkı sahibi bilgisini güncelleyin):

```
MIT License

Copyright (c) 2025 [Your Name or Organization]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

3. `[Your Name or Organization]` kısmını kendi adınız veya kuruluşunuzun adıyla değiştirin
4. Gerekirse yılı güncelleyin
5. Dosyayı kaydedin

Bu lans, başkalarının projenizi kullanmasına, değiştirmesine ve dağıtmasına izin verirken, sizi yasal sorumluluklardan korur.
