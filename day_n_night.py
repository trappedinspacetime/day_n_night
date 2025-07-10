import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from PIL import Image, ImageDraw
import io
import math
import datetime
import pytz

class DayNightMap(Gtk.Window):
    def __init__(self):
        super().__init__(title="Day and Night Map")
        self.set_default_size(400, 300)

        # Harita görüntüsünü yükle
        self.original_image = Image.open("equirectangular_earth texture.resized.jpg")
        self.image_width, self.image_height = self.original_image.size

        # GTK arayüzü
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.vbox)

        # Görüntü alanı
        self.image_area = Gtk.Image()
        self.vbox.pack_start(self.image_area, True, True, 0)

        # İlk görüntüyü güncelle
        self.update_map()

        # Her saniye haritayı güncelle (canlı güncelleme için)
        GLib.timeout_add(1000, self.update_map)  # 1000 ms = 1 saniye

    def calculate_sun_position(self):
        # Mevcut UTC zamanını al
        now = datetime.datetime.now(pytz.UTC)
        day_of_year = now.timetuple().tm_yday
        hour = now.hour + now.minute / 60.0 + now.second / 3600.0

        # Güneşin boylamını hesapla
        # 12:00 UTC'de güneş 0 boylamında (Greenwich) olur
        # Saat 15:00 UTC'de güneş 45° batı boylamında olur (15 - 12 = 3 saat, 3 * 15 = 45°)
        sun_longitude = (12 - hour) * 15  # Düzeltme: (12 - hour) ile yönü tersine çeviriyoruz

        # Güneşin deklinasyon açısını hesapla (ekliptik eğim dikkate alınarak)
        axial_tilt = 23.5
        declination = axial_tilt * math.sin(math.radians(360 * (day_of_year - 81) / 365))

        return sun_longitude, declination

    def update_map(self):
        # Güneşin konumunu hesapla
        sun_longitude, sun_declination = self.calculate_sun_position()

        # Harita üzerinde güneşin konumuna göre aydınlık ve karanlık alanları çiz
        image = self.original_image.copy()
        draw = ImageDraw.Draw(image, "RGBA")

        # Harita genişliği 360 dereceye karşılık gelir (boylam)
        # Harita yüksekliği 180 dereceye karşılık gelir (enlem)
        for x in range(self.image_width):
            lon = (x / self.image_width) * 360 - 180  # -180 ile 180 arası boylam
            for y in range(self.image_height):
                lat = 90 - (y / self.image_height) * 180  # 90 ile -90 arası enlem

                # Güneşin açısını hesapla
                sin_lat = math.sin(math.radians(lat))
                cos_lat = math.cos(math.radians(lat))
                sin_dec = math.sin(math.radians(sun_declination))
                cos_dec = math.cos(math.radians(sun_declination))
                cos_hour_angle = math.cos(math.radians(lon - sun_longitude))

                # Güneşin zenit açısını hesapla
                cos_zenith = sin_lat * sin_dec + cos_lat * cos_dec * cos_hour_angle

                # Aydınlık ve karanlık bölgeleri belirle
                if cos_zenith > 0:
                    # Aydınlık: Hiçbir şey yapma, orijinal harita görünsün
                    pass
                elif cos_zenith > -0.1:
                    # Alacakaranlık: Yumuşak bir geçiş
                    alpha = int(128 * (1 - (cos_zenith + 0.1) / 0.1))
                    draw.point((x, y), (0, 0, 0, alpha))
                else:
                    # Gece: Koyu bir katman ekle
                    draw.point((x, y), (0, 0, 0, 128))  # Yarı saydam siyah

        # Görüntüyü diske kaydetmeden belleğe al
        image = image.convert("RGB")
        with io.BytesIO() as output:
            image.save(output, format="PNG")
            data = output.getvalue()

        # Bellekteki veriyi GdkPixbuf'a çevir
        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf()

        # Görüntüyü GTK arayüzünde göster
        self.image_area.set_from_pixbuf(pixbuf)

        return True  # GLib.timeout_add için True döndürmeliyiz

    def run(self):
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
        Gtk.main()

if __name__ == "__main__":
    app = DayNightMap()
    app.run()
