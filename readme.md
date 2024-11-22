# Vestique - Smart Wardrobe Assistant 👔

Vestique is an AI-powered wardrobe management system that helps users maintain their clothing inventory, track wear patterns, and make sustainable fashion choices. Using advanced computer vision and natural language processing, it provides personalized style recommendations and helps reduce fashion waste.

## 🌟 Features

- 📸 Clothing item recognition and classification
- 👕 Wardrobe inventory management
- 📊 Wear pattern tracking and analytics
- 💡 AI-powered style recommendations
- 📧 Automated notifications for unworn items
- 🏪 Integrated marketplace for selling unworn clothes
- 🎯 Personal style advisor
- 🤖 SambaFit AI fashion agent

## 🛠️ Prerequisites

- Python 3.9+
- pip (Python package installer)
- A Gmail account for notifications
- SambaNova API key
- Brevo API key

## ⚙️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vestique.git
cd vestique
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following:
```plaintext
GMAIL_ADDRESS=your.email@gmail.com
BREVO_API_KEY=your_brevo_api_key
SAMBANOVA_API_KEY=your_sambanova_api_key
```

### 📦 Required Packages

Create a `requirements.txt` file with these dependencies:

```plaintext
streamlit
Pillow
numpy
python-dotenv
requests
scikit-learn
matplotlib
seaborn
opencv-python
langchain
langchain-community
transformers
torch
faiss-cpu
```

## 🚀 Running the Application

1. Start the application:
```bash
streamlit run app.py
```

2. Access the web interface at `http://localhost:8501`

## 📱 Using Vestique

### Initial Setup
1. Configure your email settings in the sidebar
2. Set your preferred reset period for unworn items
3. Choose capture mode (Single Item/Full Outfit)

### Adding Items
1. Use the "Capture" tab
2. Take a photo or upload an image
3. Select the item type
4. Add any additional details

### Features
- **My Wardrobe**: View and manage your clothing inventory
- **Edit Wardrobe**: Modify item details and wear counts
- **Notifications**: Set up alerts for unworn items
- **Preferences**: Customize your style preferences
- **Marketplace**: List and manage items for sale
- **Style Advisor**: Get AI-powered outfit recommendations
- **SambaFit**: Chat with AI fashion agent for outfit creation

## 🔧 Troubleshooting

### Common Issues

1. Camera not working:
   - Check browser permissions
   - Refresh the page
   - Try a different browser

2. Email notifications not sending:
   - Verify Gmail credentials
   - Check app-specific password setup
   - Confirm Brevo API key is valid

3. AI analysis failing:
   - Verify SambaNova API key
   - Check internet connection
   - Ensure image is clear and well-lit

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with SambaNova's AI platform
- Uses Meta's Llama models
- Powered by Streamlit
- Notifications via Brevo

## 📞 Support

For support, email [support@vestique.com](mailto:support@vestique.com) or create an issue in the repository.