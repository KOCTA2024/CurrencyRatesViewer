💱 Kostik – Currency Rates Viewer with Forecast
Kostik is a PyQt5 desktop application for tracking all currency exchange rates provided by the NBU API (National Bank of Ukraine) with support for charting, prediction, and configuration.

🧩 Features
🔎 Live currency viewer: view exchange rates of all currencies to UAH

📈 Historical charts: 30, 60, and 365-day visualizations

🔮 Prediction model: next-day currency rate prediction using scikit-learn linear regression

⚙️ Settings panel: full configuration persistence (auto-save & load)

🧵 Threading: fully implemented multithreading for responsive UI

🎨 Two clean themes: dark/light (via QSS)

📦 Modular codebase: follows MVC structure for clean separation of logic

🚀 Optimized performance: fast API interaction and smooth UI

🔧 Installation
Clone the repository:


git clone https://github.com/KOCTA2024/kostik.git

cd kostik

Install dependencies:


pip install -r requirements.txt




## ▶️ Running the App


python main_window.py

⚠️ Notes
The project uses the NBU public API, which has some limitations and may return unstable data.

UX is functional but can be improved.

📚 Dependencies
PyQt5

matplotlib

numpy

requests

scikit-learn

📬 Contact
Feel free to reach out for suggestions, feedback, or contributions:

Telegram: @llxldxl

