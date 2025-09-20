import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.utils import platform
from kivy.core.window import Window

import yt_dlp
import threading
import os
import re
import subprocess
import sys

# Set Kivy version (optional, but good practice)
kivy.require('2.0.0')

# --- Function to ensure latest yt-dlp (remains largely the same) ---
def ensure_latest_yt_dlp():
    """
    Kiểm tra phiên bản yt-dlp hiện tại và tự động nâng cấp nếu cần.
    In thông báo ra console.
    Trả về True nếu thành công hoặc đã là phiên bản mới nhất, False nếu có lỗi.
    """
    print("--- Đang kiểm tra và cập nhật yt-dlp ---")
    try:
        # Kiểm tra xem yt-dlp có trong danh sách các gói đã cài đặt không
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"], capture_output=True, text=True, check=False
        )
        installed_packages = result.stdout

        if "yt-dlp" in installed_packages:
            print("Đã tìm thấy yt-dlp. Đang kiểm tra cập nhật...")
            update_result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True, text=True
            )

            if "Requirement already satisfied" in update_result.stdout:
                print("yt-dlp đã ở phiên bản mới nhất.")
            elif update_result.returncode == 0:
                print("Đã nâng cấp yt-dlp thành công!")
            else:
                print(f"Không thể nâng cấp yt-dlp. Thông báo: \n{update_result.stdout}\n{update_result.stderr}")
                return False
        else:
            print("yt-dlp chưa được cài đặt. Đang tiến hành cài đặt...")
            install_result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "yt-dlp"],
                capture_output=True, text=True
            )
            if install_result.returncode == 0:
                print("Đã cài đặt yt-dlp thành công!")
            else:
                print(f"Lỗi khi cài đặt yt-dlp: \n{install_result.stdout}\n{install_result.stderr}")
                return False

    except FileNotFoundError:
        print("Lỗi: Python hoặc pip không được tìm thấy. Đảm bảo chúng đã được cài đặt và thêm vào PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi chạy lệnh pip: {e.stderr}")
        return False
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn trong quá trình kiểm tra/cập nhật yt-dlp: {e}")
        return False
    finally:
        print("--- Hoàn thành kiểm tra yt-dlp ---")
    return True

# --- Kivy Language (KV) String for UI Definition ---
KV_CODE = """
#:import Window kivy.core.window.Window

<StartWindow>:
    orientation: 'vertical'
    padding: 20
    spacing: 20
    size_hint: None, None
    size: 400, 300
    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
    
    canvas.before:
        Color:
            rgba: 112, 112, 112, 0.76
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "Chọn nền tảng để tải video:"
        font_size: 18
        bold: True
        size_hint_y: None
        pos_hint: {'y': 40}
        height: self.texture_size[1]

    Button:
        text: "Tải từ YouTube"
        font_size: 14
        size_hint: None, None
        size: 200, 40
        pos_hint: {'center_x': 0.5}
        on_release: app.show_youtube_gui()

    Button:
        text: "Tải từ TikTok"
        font_size: 14
        size_hint: None, None
        size: 200, 40
        pos_hint: {'center_x': 0.5}
        on_release: app.show_tiktok_gui()

<CommonDownloadScreen>:
    orientation: 'vertical'
    padding: 20
    spacing: 10

    Label:
        id: title_label
        text: "" # Set by specific screen
        font_size: 20
        bold: True
        size_hint_y: None
        height: self.texture_size[1]

    Label:
        id: subtitle_label
        text: "" # Set by specific screen
        font_size: 12
        size_hint_y: None
        height: self.texture_size[1]

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: dp(100) # Fixed height for URL and Dir input
        spacing: 5

        Label:
            id: url_label
            text: "" # Set by specific screen
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            halign: 'left'
            valign: 'middle'

        TextInput:
            id: url_input
            hint_text: "" # Set by specific screen
            multiline: False
            size_hint_y: None
            height: dp(35)

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: dp(100) # Fixed height for URL and Dir input
        spacing: 5

        Label:
            text: "Thư Mục Lưu:"
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            halign: 'left'
            valign: 'middle'

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(35)
            spacing: 5

            TextInput:
                id: dir_input
                multiline: False
                size_hint_x: 0.8
                height: dp(35)

            Button:
                text: "Duyệt..."
                size_hint_x: 0.2
                height: dp(35)
                on_release: root.browse_directory()

    Label:
        id: format_label
        text: "" # Set by specific screen
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'

    Spinner:
        id: format_spinner
        text: "" # Set by specific screen
        values: [] # Set by specific screen
        size_hint: None, None
        size: 300, 40
        pos_hint: {'center_x': 0.5}

    Button:
        id: download_button
        text: "Tải Xuống"
        font_size: 15
        bold: True
        size_hint: None, None
        size: 200, 40
        pos_hint: {'center_x': 0.5}
        background_normal: ''
        background_color: 0.29, 0.68, 0.31, 1 # #4CAF50
        on_release: root.start_download_thread()
        disabled: True # Disabled by default

    Label:
        id: status_label
        text: "Đang khởi tạo..."
        color: 0, 0, 1, 1 # Blue
        size_hint_y: None
        height: self.texture_size[1]

    ScrollView:
        size_hint: 1, 1
        do_scroll_x: False
        bar_width: 10
        bar_color: 0.5, 0.5, 0.5, 1
        # The Label below must be a direct child of ScrollView for scrolling to work.
        # Its properties (text_size, halign, valign) belong directly to it.
        Label:
            id: log_text
            text: "Sẵn sàng..."\n
            text_size: self.width, None # This must be set correctly for text wrapping and height calculation
            halign: 'left'
            valign: 'top'
            padding: 10, 10
            size_hint_y: None # Important: This allows the label to expand vertically within the ScrollView
            height: self.texture_size[1] # Automatically adjust height based on content
            markup: True # Enable markup for color tags

    Button:
        text: "Quay Lại"
        size_hint: None, None
        size: 150, 40
        pos_hint: {'center_x': 0.5}
        on_release: app.show_start_window()

"""
Builder.load_string(KV_CODE)


# --- Common Download Screen Class ---
class CommonDownloadScreen(BoxLayout):
    url_input = ObjectProperty(None)
    dir_input = ObjectProperty(None)
    format_spinner = ObjectProperty(None)
    download_button = ObjectProperty(None)
    status_label = ObjectProperty(None)
    log_text = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Bind properties from KV to Python properties
        self.url_input = self.ids.url_input
        self.dir_input = self.ids.dir_input
        self.format_spinner = self.ids.format_spinner
        self.download_button = self.ids.download_button
        self.status_label = self.ids.status_label
        self.log_text = self.ids.log_text

        self.log_text.text = "[color=000000]Sẵn sàng...\n[/color]" # Default black text

    def browse_directory(self):
        # Kivy's file chooser is more complex than simple filedialog.askdirectory
        # For simplicity, we'll use a basic popup for now.
        # A full file chooser would require a separate Kivy screen/widget.
        # On desktop, we can use tkinter for filedialog, but it's not cross-platform for Kivy.
        # For a truly cross-platform Kivy app, consider plyer.filechooser or implementing a custom one.

        # Fallback for desktop platforms to use tkinter's filedialog
        if platform == 'win' or platform == 'linux' or platform == 'macosx':
            # Get the root window from Kivy app, not necessary to explicitly hide/show like in original code
            # Tkinter filedialog often handles its own windowing.
            folder_selected = filedialog.askdirectory()
            if folder_selected:
                self.dir_input.text = folder_selected
        else:
            # For mobile or other platforms, a simple text input or a more complex Kivy file chooser is needed.
            # For this example, we'll just show a message.
            self.show_message_popup("Thông báo", "Chức năng duyệt thư mục đầy đủ chưa được hỗ trợ trên nền tảng này. Vui lòng nhập đường dẫn thủ công.")
            print("File dialog not fully implemented for this platform in Kivy example.")


    def show_message_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                      size_hint=(0.8, 0.4), auto_dismiss=True)
        popup.open()

    def log_message(self, message, append=True, color=None):
        # Use Clock.schedule_once to update GUI from a non-GUI thread
        def update_log(dt):
            if not append:
                self.log_text.text = ""
            
            color_tag_start = ""
            color_tag_end = ""
            if color == "red":
                color_tag_start = "[color=ff0000]"
                color_tag_end = "[/color]"
            elif color == "blue":
                color_tag_start = "[color=0000ff]"
                color_tag_end = "[/color]"
            elif color == "green":
                color_tag_start = "[color=00ff00]"
                color_tag_end = "[/color]"
            elif color == "orange":
                color_tag_start = "[color=ffa500]"
                color_tag_end = "[/color]"
            else:
                color_tag_start = "[color=000000]" # Default to black
                color_tag_end = "[/color]"

            self.log_text.text += f"{color_tag_start}{message}\n{color_tag_end}"
            # Scroll to the end
            self.log_text.parent.scroll_y = 0 # ScrollView's scroll_y property
            self.log_text.texture_update() # Ensure texture is updated for accurate height calculation
            self.log_text.height = self.log_text.texture_size[1] # Update height to fit content
            
        Clock.schedule_once(update_log)

    def update_status(self, message, color="blue"):
        # Use Clock.schedule_once to update GUI from a non-GUI thread
        def update_status_label(dt):
            self.status_label.text = message
            if color == "red":
                self.status_label.color = (1, 0, 0, 1)
            elif color == "blue":
                self.status_label.color = (0, 0, 1, 1)
            elif color == "green":
                self.status_label.color = (0, 1, 0, 1)
            else:
                self.status_label.color = (0, 0, 0, 1) # Default to black
        Clock.schedule_once(update_status_label)

    def _start_yt_dlp_check_thread(self):
        self.update_status("Đang kiểm tra và cập nhật yt-dlp...", "blue")
        check_thread = threading.Thread(target=self._run_yt_dlp_check)
        check_thread.start()

    def _run_yt_dlp_check(self):
        self.log_message("--- Khởi động: Đang kiểm tra yt-dlp ---", append=False)
        success = ensure_latest_yt_dlp()

        def post_check_update(dt):
            if success:
                self.update_status("yt-dlp đã sẵn sàng.", "green")
                self.download_button.disabled = False
                self.download_button.text = "Tải Xuống"
                self.log_message("yt-dlp đã được kiểm tra/cập nhật thành công.")
            else:
                self.update_status("Lỗi: Không thể đảm bảo yt-dlp được cập nhật. Vui lòng kiểm tra console.", "red")
                self.download_button.disabled = False # Still allow download, but warn
                self.download_button.text = "Tải Xuống (Lỗi cập nhật)"
                self.log_message("Lỗi khi kiểm tra/cập nhật yt-dlp. Kiểm tra thông báo lỗi trong console.", color="red")
        
        Clock.schedule_once(post_check_update)

    def start_download_thread(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def hook_progress(self, d):
        def update_progress(dt):
            if d['status'] == 'downloading':
                p = d.get('_percent_str', 'N/A')
                filename = os.path.basename(d.get('filename', ''))
                self.update_status(f"Đang tải: {filename} - {p}", "blue")
                self.log_message(f"Tiến độ: {p}", color="orange")
            elif d['status'] == 'finished':
                self.update_status("Đang xử lý hậu kỳ (nếu có)...", "green")
                self.log_message(f"Đã hoàn thành tải xuống {d['filename']}.")
            elif d['status'] == 'error':
                self.update_status("Có lỗi xảy ra khi tải xuống.", "red")
                self.log_message(f"Lỗi: {d.get('error', 'Không rõ lỗi.')}", color="red")
        Clock.schedule_once(update_progress)


# --- YouTube Downloader GUI ---
class YouTubeDownloaderGUI(CommonDownloadScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.title_label.text = "Tải Video/Audio YouTube"
        self.ids.subtitle_label.text = "Sử dụng yt-dlp"
        self.ids.url_label.text = "Nhập URL Video/Playlist YouTube:"
        self.ids.url_input.hint_text = "Ví dụ: https://www.youtube.com/watch?v=..."

        self.ids.format_label.text = "Chọn Độ Phân Giải/Định Dạng:"
        self.format_options = [
            "Cao nhất (Video + Audio MP4)",
            "Cao nhất (Video riêng MP4)",
            "Cao nhất (Audio riêng MP3)",
            "1080p (MP4)",
            "720p (MP4)",
            "480p (MP4)",
            "360p (MP4)"
        ]
        self.ids.format_spinner.values = self.format_options
        self.ids.format_spinner.text = self.format_options[0] # Set default selection

        default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube_Downloads")
        self.ids.dir_input.text = default_download_dir
        
        self._start_yt_dlp_check_thread() # Start check when screen is initialized

    def start_download_thread(self):
        url = self.ids.url_input.text.strip()
        download_dir = self.ids.dir_input.text.strip()
        selected_format_option = self.ids.format_spinner.text

        if not url:
            self.show_message_popup("Lỗi", "Vui lòng nhập URL video/playlist YouTube.")
            return
        if not download_dir:
            self.show_message_popup("Lỗi", "Vui lòng chọn thư mục lưu.")
            return
        
        # Kiểm tra URL YouTube
        if not re.match(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/.+$", url):
            self.show_message_popup("Lỗi", "URL không phải của YouTube hợp lệ. Vui lòng sử dụng giao diện TikTok cho URL TikTok nếu cần.")
            return

        self.ids.download_button.disabled = True
        self.ids.download_button.text = "Đang tải..."
        self.update_status("Đang chuẩn bị tải xuống...", "blue")
        self.log_message("--- Bắt đầu tải xuống nội dung YouTube ---")

        download_thread = threading.Thread(target=self.download_youtube_content,
                                            args=(url, download_dir, selected_format_option))
        download_thread.start()

    def download_youtube_content(self, url, download_dir, selected_format_option):
        try:
            os.makedirs(download_dir, exist_ok=True)
            self.log_message(f"Thư mục lưu: {os.path.abspath(download_dir)}")

            ydl_opts = {
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'progress_hooks': [self.hook_progress],
                'postprocessors': [],
                'merge_output_format': 'mp4',
            }

            if selected_format_option == "Cao nhất (Video + Audio MP4)":
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif selected_format_option == "Cao nhất (Video riêng MP4)":
                ydl_opts['format'] = 'bestvideo[ext=mp4]/best[ext=mp4]'
            elif selected_format_option == "Cao nhất (Audio riêng MP3)":
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                })
                ydl_opts['outtmpl'] = os.path.join(download_dir, '%(title)s.%(ext)s')
            elif "p (MP4)" in selected_format_option:
                height = int(selected_format_option.split('p')[0])
                ydl_opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'

            if "playlist?list=" in url or "/playlist/" in url:
                self.log_message(f"Phát hiện URL Playlist YouTube. Đang tải toàn bộ playlist...")
                ydl_opts['noplaylist'] = False
                ydl_opts['outtmpl'] = os.path.join(download_dir, '%(playlist_title)s', '%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)

                if 'entries' in info_dict:
                    self.update_status(f"Hoàn thành tải playlist! Đã tải {len(info_dict['entries'])} mục.", "green")
                else:
                    self.update_status("Hoàn thành tải xuống!", "green")

                self.log_message("--- Tải xuống hoàn tất ---")

        except yt_dlp.utils.DownloadError as e:
            error_message = f"Lỗi tải xuống: {e}"
            self.log_message(error_message, color="red")
            self.update_status("Tải xuống thất bại!", "red")
            self.show_message_popup("Lỗi Tải Xuống", error_message)
        except Exception as e:
            error_message = f"Đã xảy ra lỗi không xác định: {e}"
            self.log_message(error_message, color="red")
            self.update_status("Tải xuống thất bại!", "red")
            self.show_message_popup("Lỗi", error_message)
        finally:
            Clock.schedule_once(lambda dt: self.ids.download_button.setter('disabled')(self.ids.download_button, False))
            Clock.schedule_once(lambda dt: self.ids.download_button.setter('text')(self.ids.download_button, "Tải Xuống"))


# --- TikTok Downloader GUI ---
class TikTokDownloaderGUI(CommonDownloadScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.title_label.text = "Tải Video TikTok"
        self.ids.subtitle_label.text = "Sử dụng yt-dlp (hỗ trợ xóa watermark)"
        self.ids.url_label.text = "Nhập URL Video TikTok:"
        self.ids.url_input.hint_text = "Ví dụ: https://www.tiktok.com/@user/video/..."

        self.ids.format_label.text = "Định dạng video:"
        self.format_options = ["Mặc định (Video MP4)"] # Đơn giản hóa cho TikTok
        self.ids.format_spinner.values = self.format_options
        self.ids.format_spinner.text = self.format_options[0]

        default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "TikTok_Downloads")
        self.ids.dir_input.text = default_download_dir
        
        self._start_yt_dlp_check_thread() # Start check when screen is initialized

    def start_download_thread(self):
        url = self.ids.url_input.text.strip()
        download_dir = self.ids.dir_input.text.strip()
        
        if not url:
            self.show_message_popup("Lỗi", "Vui lòng nhập URL video TikTok.")
            return
        if not download_dir:
            self.show_message_popup("Lỗi", "Vui lòng chọn thư mục lưu.")
            return
        
        # Kiểm tra URL TikTok
        if not re.match(r"^(https?://)?(www\.)?(tiktok\.com)/.+$", url):
            self.show_message_popup("Lỗi", "URL không phải của TikTok hợp lệ. Vui lòng sử dụng giao diện YouTube cho URL YouTube nếu cần.")
            return

        self.ids.download_button.disabled = True
        self.ids.download_button.text = "Đang tải..."
        self.update_status("Đang chuẩn bị tải xuống...", "blue")
        self.log_message("--- Bắt đầu tải xuống nội dung TikTok ---")

        download_thread = threading.Thread(target=self.download_tiktok_content,
                                            args=(url, download_dir))
        download_thread.start()

    def download_tiktok_content(self, url, download_dir):
        try:
            os.makedirs(download_dir, exist_ok=True)
            self.log_message(f"Thư mục lưu: {os.path.abspath(download_dir)}")

            ydl_opts = {
                'outtmpl': os.path.join(download_dir, '%(uploader)s - %(title)s.%(ext)s'),
                'noplaylist': True,
                'progress_hooks': [self.hook_progress],
                'postprocessors': [],
                'merge_output_format': 'mp4',
                'format': 'bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best',
                'geo_bypass': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                self.update_status("Hoàn thành tải xuống!", "green")
                self.log_message("--- Tải xuống hoàn tất ---")

        except yt_dlp.utils.DownloadError as e:
            error_message = f"Lỗi tải xuống: {e}"
            self.log_message(error_message, color="red")
            self.update_status("Tải xuống thất bại!", "red")
            self.show_message_popup("Lỗi Tải Xuống", error_message)
        except Exception as e:
            error_message = f"Đã xảy ra lỗi không xác định: {e}"
            self.log_message(error_message, color="red")
            self.update_status("Tải xuống thất bại!", "red")
            self.show_message_popup("Lỗi", error_message)
        finally:
            Clock.schedule_once(lambda dt: self.ids.download_button.setter('disabled')(self.ids.download_button, False))
            Clock.schedule_once(lambda dt: self.ids.download_button.setter('text')(self.ids.download_button, "Tải Xuống"))


# --- Main Kivy Application ---
class UniversalVideoDownloaderApp(App):
    def build(self):
        self.title = "Universal Video Downloader"
        # Set window size and make it non-resizable initially
        Window.size = (400, 300)
        Window.bind(on_resize=self._on_window_resize)
        self.resizable = False # Custom flag to control resizability

        # Set the application icon (Kivy way)
        # Note: Kivy expects a path to an image file.
        # Ensure 'D:/Python projects/asset/Mahiru.ico' exists or provide a default.
        # If .ico is not supported directly, convert it to .png or .jpg.
        try:
            self.icon = "D:/Python projects/asset/Mahiru.ico"
        except Exception as e:
            print(f"Could not load icon: {e}. Using default Kivy icon.")
            # Fallback to a default Kivy icon or no icon if the path is invalid/format unsupported.
            self.icon = '' # No icon

        self.start_window = StartWindow()
        self.youtube_gui = YouTubeDownloaderGUI()
        self.tiktok_gui = TikTokDownloaderGUI()

        self.root_layout = BoxLayout(orientation='vertical')
        self.root_layout.add_widget(self.start_window)
        return self.root_layout

    def _on_window_resize(self, window, width, height):
        # Prevent resizing if self.resizable is False
        if not self.resizable:
            # Revert to the desired size if resizing is not allowed
            # This is a bit of a hack for strict non-resizing.
            # A better way might be to set min_size and max_size for the Window (Kivy 2.1.0+).
            # For now, it will fight manual resizing.
            if Window.size != (400, 300) and not self.resizable:
                Window.size = (400, 300)
        # If resizable is True, allow it to change size
        else:
            pass # Do nothing, allow Window to handle resize

    def show_youtube_gui(self):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.youtube_gui)
        Window.size = (700, 600)
        self.resizable = True # Allow resizing for download screens

    def show_tiktok_gui(self):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.tiktok_gui)
        Window.size = (700, 600)
        self.resizable = True # Allow resizing for download screens

    def show_start_window(self):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.start_window)
        Window.size = (400, 300)
        self.resizable = False # Disable resizing for start window


class StartWindow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


if __name__ == "__main__":
    # For Windows, if using tkinter.filedialog, ensure it's imported
    # and that the mainloop is not started for tkinter.
    # Kivy's Clock.schedule_once is used to update GUI from threads.
    if platform == 'win' or platform == 'linux' or platform == 'macosx':
        # Tkinter is only imported if needed for filedialog on desktop
        import tkinter as tk
        from tkinter import filedialog
        # Initialize Tkinter root, but don't run its mainloop
        # This is a common pattern to use Tkinter dialogs with other GUI frameworks.
        tk_root = tk.Tk()
        tk_root.withdraw() # Hide the main Tkinter window

    app = UniversalVideoDownloaderApp()
    app.run()