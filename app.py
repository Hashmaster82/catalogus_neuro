import os
import json
import shutil
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, Text, Menu
from datetime import datetime

SETTINGS_FILE = "settings.json"
ONLINE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "online.json")
BASE_FILE = None
TOP_FILE = None


def load_or_create_settings():
    global BASE_FILE, TOP_FILE
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
            base_path = settings.get("base_path")
            if base_path and os.path.exists(base_path):
                BASE_FILE = base_path
                TOP_FILE = os.path.join(os.path.dirname(BASE_FILE), "top.json")
                return

    root_temp = ttk.Window(themename="cosmo")
    root_temp.withdraw()
    messagebox.showinfo("Первый запуск", "Пожалуйста, выберите папку для хранения базы данных.")
    folder = filedialog.askdirectory(title="Выберите папку для базы данных")
    root_temp.destroy()

    if not folder:
        exit()

    BASE_FILE = os.path.join(folder, "base.json")
    TOP_FILE = os.path.join(folder, "top.json")

    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"base_path": BASE_FILE}, f, ensure_ascii=False, indent=4)

    if not os.path.exists(BASE_FILE):
        with open(BASE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
    if not os.path.exists(TOP_FILE):
        with open(TOP_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)


def load_records(filename):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить {filename}:\n{e}")
        return []


def save_records(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить {filename}:\n{e}")


def update_top_record(record, is_top):
    top_records = load_records(TOP_FILE)
    ids = [r.get("id") for r in top_records]
    if is_top and record["id"] not in ids:
        top_records.append(record)
    elif not is_top and record["id"] in ids:
        top_records = [r for r in top_records if r["id"] != record["id"]]
    save_records(TOP_FILE, top_records)


def generate_id(records):
    if not records:
        return 1
    return max(r.get("id", 0) for r in records) + 1


def sort_records_by_date(records):
    def parse_date(record):
        date_str = record.get("Дата", "").strip()
        if not date_str:
            return datetime.min
        try:
            return datetime.strptime(date_str, "%d.%m.%Y")
        except ValueError:
            return datetime.min
    return sorted(records, key=parse_date, reverse=True)


def create_backup():
    if not BASE_FILE or not os.path.exists(BASE_FILE):
        messagebox.showwarning("Предупреждение", "База данных не инициализирована.")
        return

    backup_dir = os.path.dirname(BASE_FILE)
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    backup_base = os.path.join(backup_dir, f"base_backup_{timestamp}.json")
    backup_top = os.path.join(backup_dir, f"top_backup_{timestamp}.json")

    try:
        shutil.copy2(BASE_FILE, backup_base)
        shutil.copy2(TOP_FILE, backup_top)
        messagebox.showinfo("Успех", f"Резервная копия создана:\n{backup_base}\n{backup_top}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать резервную копию:\n{e}")


def add_to_online(record):
    """Добавляет запись в online.json, если её там ещё нет"""
    online_records = load_records(ONLINE_FILE)
    existing_ids = {r.get("id") for r in online_records}
    if record["id"] not in existing_ids:
        online_records.append(record)
        save_records(ONLINE_FILE, online_records)
        messagebox.showinfo("Успех", "Запись добавлена в онлайн-базу.", parent=ttk.Window.instance)
    else:
        messagebox.showinfo("Информация", "Запись уже есть в онлайн-базе.", parent=ttk.Window.instance)


def delete_record(record_id, app):
    """Удаляет запись из всех баз: base, top, online"""
    # Удаляем из основной базы
    base_records = load_records(BASE_FILE)
    base_records = [r for r in base_records if r["id"] != record_id]
    save_records(BASE_FILE, base_records)

    # Удаляем из top
    top_records = load_records(TOP_FILE)
    top_records = [r for r in top_records if r["id"] != record_id]
    save_records(TOP_FILE, top_records)

    # Удаляем из online
    online_records = load_records(ONLINE_FILE)
    online_records = [r for r in online_records if r["id"] != record_id]
    save_records(ONLINE_FILE, online_records)

    messagebox.showinfo("Успех", "Запись удалена из всех баз.")
    app.load_and_show_all()


class RecordFormWindow:
    def __init__(self, parent, app, record=None):
        self.parent = parent
        self.app = app
        self.record = record
        self.win = ttk.Toplevel(parent)
        self.win.title("Добавить запись" if record is None else "Редактировать запись")
        self.win.geometry("800x800")
        self.win.transient(parent)

        title = "Добавить новую запись" if record is None else "Редактировать запись"
        ttk.Label(self.win, text=title, font=("Arial", 14, "bold")).pack(pady=(15, 20))

        main_frame = ttk.Frame(self.win)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        fields = ["Название", "Ярлык", "Описание", "Расположение", "Дата"]
        self.entries = {}

        for field in fields:
            label = ttk.Label(main_frame, text=field, font=("Arial", 11, "bold"))
            label.pack(anchor="w", pady=(5, 2))
            if field in ["Описание", "Расположение"]:
                text = Text(main_frame, height=5, width=80, font=("Arial", 10), relief="solid", borderwidth=1)
                text.pack(fill="x", pady=(0, 10))
                self.entries[field] = text
            else:
                entry = ttk.Entry(main_frame, font=("Arial", 10))
                entry.pack(fill="x", pady=(0, 10))
                self.entries[field] = entry

        self.top_var = ttk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Добавить в Топ", variable=self.top_var, bootstyle="round-toggle").pack(anchor="w", pady=(5, 15))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(10, 0))
        ttk.Button(btn_frame, text="Сохранить", command=self.save, bootstyle=SUCCESS, width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.win.destroy, bootstyle=SECONDARY, width=12).pack(side="left", padx=10)

        if record:
            self.fill_fields(record)
        else:
            current_date = datetime.now().strftime("%d.%m.%Y")
            self.entries["Дата"].insert(0, current_date)

    def fill_fields(self, record):
        for field in ["Название", "Ярлык", "Дата"]:
            self.entries[field].insert(0, record.get(field, ""))
        for field in ["Описание", "Расположение"]:
            self.entries[field].insert("1.0", record.get(field, ""))
        self.top_var.set(record.get("В Топ", False))

    def get_field_value(self, field):
        widget = self.entries[field]
        if isinstance(widget, Text):
            return widget.get("1.0", "end-1c").strip()
        else:
            return widget.get().strip()

    def save(self):
        data = {}
        for field in ["Название", "Ярлык", "Описание", "Расположение", "Дата"]:
            data[field] = self.get_field_value(field)
        data["В Топ"] = self.top_var.get()

        if not data["Название"]:
            messagebox.showwarning("Внимание", "Поле 'Название' обязательно.", parent=self.win)
            return

        if data["Дата"]:
            try:
                datetime.strptime(data["Дата"], "%d.%m.%Y")
            except ValueError:
                messagebox.showerror("Ошибка", "Дата должна быть в формате ДД.ММ.ГГГГ", parent=self.win)
                return

        records = load_records(BASE_FILE)

        if self.record is None:
            data["id"] = generate_id(records)
            records.append(data)
        else:
            for i, r in enumerate(records):
                if r["id"] == self.record["id"]:
                    data["id"] = r["id"]
                    records[i] = data
                    break

        save_records(BASE_FILE, records)
        update_top_record(data, data["В Топ"])
        self.win.destroy()
        self.app.load_and_show_all()


class CatalogusNeuroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Catalogus Neuro")
        self.root.state('zoomed')

        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 11))
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))

        control_frame = ttk.Frame(root)
        control_frame.pack(fill="x", padx=30, pady=15)

        self.search_var = ttk.StringVar()
        self.search_entry = ttk.Entry(control_frame, textvariable=self.search_var, font=("Arial", 12))
        self.search_entry.pack(fill="x", pady=(0, 15))
        self.search_entry.bind("<KeyRelease>", self.on_search)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Список", command=self.show_all, bootstyle=PRIMARY, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Онлайн", command=self.show_online, bootstyle=INFO, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Добавить", command=self.open_add_form, bootstyle=SUCCESS, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Лидеры", command=self.show_top, bootstyle=INFO, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Настройки", command=self.open_settings, bootstyle=WARNING, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Резерв", command=create_backup, bootstyle=WARNING, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Инфо", command=self.show_info, bootstyle=SECONDARY, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Выход", command=self.exit_app, bootstyle=DANGER, width=12).pack(side="left", padx=5)

        self.content_frame = ttk.Frame(root)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.records = []
        self.current_view = "all"
        self.sort_column = None
        self.sort_reverse = False
        self.right_clicked_item = None  # Для хранения записи под курсором

        self.show_list_view()

    def exit_app(self):
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти из приложения?"):
            self.root.destroy()

    def show_list_view(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.tree_frame = ttk.Frame(self.content_frame)
        self.tree_frame.pack(fill="both", expand=True)

        columns = ("Название", "Ярлык", "Описание", "Расположение", "Дата", "В Топ")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", height=20)

        self.tree.column("Название", width=150, anchor="center", stretch=False)
        self.tree.column("Ярлык", width=100, anchor="center", stretch=False)
        self.tree.column("Описание", width=300, anchor="w", stretch=True)
        self.tree.column("Расположение", width=200, anchor="w", stretch=False)
        self.tree.column("Дата", width=100, anchor="center", stretch=False)
        self.tree.column("В Топ", width=60, anchor="center", stretch=False)

        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col))

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.on_edit)
        self.tree.bind("<Button-3>", self.on_right_click)  # Правый клик

        self.load_and_show_all()

    def on_right_click(self, event):
        """Обработка правого клика — показ контекстного меню"""
        item = self.tree.identify_row(event.y)
        if not item:
            return

        self.right_clicked_item = item
        record_id = int(item)

        # Найдём запись в основной базе (все записи хранятся в self.records)
        record = next((r for r in self.records if r["id"] == record_id), None)
        if not record:
            return

        # Создаём контекстное меню
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Добавить в онлайн", command=lambda: self.add_record_to_online(record))
        menu.add_command(label="Удалить запись", command=lambda: self.confirm_delete_record(record_id))
        menu.post(event.x_root, event.y_root)

    def add_record_to_online(self, record):
        add_to_online(record)

    def confirm_delete_record(self, record_id):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись из всех баз?"):
            delete_record(record_id, self)

    def sort_by_column(self, col):
        """Сортировка по указанному столбцу с переключением направления."""
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.sort_column = col

        if self.current_view == "all":
            data = self.records.copy()
        elif self.current_view == "top":
            data = load_records(TOP_FILE)
        elif self.current_view == "online":
            data = load_records(ONLINE_FILE)
        else:
            data = []

        def get_sort_value(record):
            val = record.get(col, "")
            if col == "Дата":
                try:
                    return datetime.strptime(val, "%d.%m.%Y")
                except ValueError:
                    return datetime.min
            elif col == "В Топ":
                return record.get("В Топ", False)
            else:
                return str(val).lower()

        data.sort(key=get_sort_value, reverse=self.sort_reverse)

        self.tree.delete(*self.tree.get_children())
        for rec in data:
            self.insert_record_into_tree(rec)

    def on_search(self, event=None):
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        if self.current_view == "all":
            source = self.records
        elif self.current_view == "top":
            source = load_records(TOP_FILE)
        elif self.current_view == "online":
            source = load_records(ONLINE_FILE)
        else:
            source = []
        for rec in source:
            if (query in rec.get("Название", "").lower() or
                query in rec.get("Ярлык", "").lower() or
                query in rec.get("Описание", "").lower()):
                self.insert_record_into_tree(rec)

    def insert_record_into_tree(self, rec):
        top_status = "✅" if rec.get("В Топ", False) else "⬜"
        values = (
            rec.get("Название", ""),
            rec.get("Ярлык", ""),
            rec.get("Описание", ""),
            rec.get("Расположение", "")[:30] + "..." if len(rec.get("Расположение", "")) > 30 else rec.get("Расположение", ""),
            rec.get("Дата", ""),
            top_status
        )
        self.tree.insert("", "end", iid=rec["id"], values=values)

    def load_and_show_all(self):
        self.records = load_records(BASE_FILE)
        self.records = sort_records_by_date(self.records)
        if self.current_view == "all":
            self.show_all()
        elif self.current_view == "top":
            self.show_top()
        elif self.current_view == "online":
            self.show_online()

    def show_all(self):
        self.current_view = "all"
        self.sort_column = None
        self.sort_reverse = False
        self.tree.delete(*self.tree.get_children())
        for rec in self.records:
            self.insert_record_into_tree(rec)

    def show_top(self):
        self.current_view = "top"
        self.sort_column = None
        self.sort_reverse = False
        self.tree.delete(*self.tree.get_children())
        top_records = load_records(TOP_FILE)
        top_records = sort_records_by_date(top_records)
        for rec in top_records:
            self.insert_record_into_tree(rec)

    def show_online(self):
        self.current_view = "online"
        self.sort_column = None
        self.sort_reverse = False
        self.tree.delete(*self.tree.get_children())
        online_records = load_records(ONLINE_FILE)
        online_records = sort_records_by_date(online_records)
        for rec in online_records:
            self.insert_record_into_tree(rec)

    def open_add_form(self):
        RecordFormWindow(self.root, self, record=None)

    def on_edit(self, event):
        item = self.tree.selection()
        if not item:
            return
        record_id = int(item[0])
        record = next((r for r in self.records if r["id"] == record_id), None)
        if record:
            RecordFormWindow(self.root, self, record=record)

    def open_settings(self):
        SettingsWindow(self.root, self)

    def show_info(self):
        messagebox.showinfo("Информация", "Catalogus Neuro\nВерсия: 1.0\nАвтор: Разин Г.В.")


class SettingsWindow:
    def __init__(self, parent, app):
        self.app = app
        self.win = ttk.Toplevel(parent)
        self.win.title("Настройки")
        self.win.geometry("600x180")
        self.win.transient(parent)
        self.win.grab_set()

        ttk.Label(self.win, text="Текущий путь к базе данных:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 5))

        path_frame = ttk.Frame(self.win)
        path_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.path_var = ttk.StringVar(value=BASE_FILE or "Не задан")
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, state="readonly", width=70)
        path_entry.pack(side="left", fill="x", expand=True, ipady=2)

        btn_frame = ttk.Frame(self.win)
        btn_frame.pack(pady=(0, 15))
        ttk.Button(btn_frame, text="Изменить путь", command=self.change_path, bootstyle=WARNING).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Закрыть", command=self.win.destroy, bootstyle=SECONDARY).pack(side="left", padx=10)

    def change_path(self):
        folder = filedialog.askdirectory(title="Выберите папку для базы данных")
        if not folder:
            return

        global BASE_FILE, TOP_FILE
        BASE_FILE = os.path.join(folder, "base.json")
        TOP_FILE = os.path.join(folder, "top.json")

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"base_path": BASE_FILE}, f, ensure_ascii=False, indent=4)

        if not os.path.exists(BASE_FILE):
            with open(BASE_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        if not os.path.exists(TOP_FILE):
            with open(TOP_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

        self.path_var.set(BASE_FILE)
        self.app.load_and_show_all()
        messagebox.showinfo("Успех", "Путь к базе данных успешно обновлён!")


if __name__ == "__main__":
    load_or_create_settings()
    root = ttk.Window(themename="cosmo")
    app = CatalogusNeuroApp(root)
    root.mainloop()