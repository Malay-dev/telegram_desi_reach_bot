# DesiReach - Artisan Marketing Bot 🎨

A Telegram bot powered by Google's Gemini AI that helps Indian artisans and craftsmen create professional marketing content for their products. The bot generates high-quality product images and compelling social media captions to help artisans expand their digital presence.

## ✨ Features

- **AI-Powered Marketing Content**: Generate professional marketing images and captions using Gemini AI
- **Interactive Image Selection**: Browse through 3 generated marketing images with navigation controls
- **Caption Customization**: Choose from 3 different marketing captions with hashtags and emojis
- **Conversational AI**: Chat with the bot for marketing advice and product guidance
- **Cultural Sensitivity**: Designed specifically for Indian artisans with culturally relevant content
- **Telegram Integration**: Easy-to-use interface through Telegram

## 🚀 How It Works

1. **Upload Product Image**: Send a photo of your product to the bot
2. **Provide Description**: Describe your product, target audience, and style
3. **Browse Generated Images**: Navigate through 3 AI-generated marketing images
4. **Select Caption**: Choose from 3 professionally crafted captions with hashtags
5. **Get Final Post**: Receive your complete social media post ready for sharing

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Google Gemini API Key
- FastAPI for webhook deployment

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/artisan-marketing-bot.git
   cd artisan-marketing-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   BOT_USERNAME=your_bot_username
   WEBHOOK_URL=your_webhook_url  # For production deployment
   ```

4. **Create required directories**
   ```bash
   mkdir -p tmp/received tmp/generated logs
   ```

5. **Run the bot**
   
   For local development (polling):
   ```bash
   # Uncomment the polling line in main.py
   python main.py
   ```
   
   For production (webhook):
   ```bash
   uvicorn main:server --host 0.0.0.0 --port 8000
   ```

### Production Deployment

The bot is configured to run with webhooks for production deployment. You can deploy it on platforms like:

- **Railway**: Simple deployment with automatic scaling
- **Heroku**: Easy deployment with Procfile
- **DigitalOcean**: VPS deployment with Docker
- **Google Cloud Run**: Serverless container deployment

## 📋 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot and begin conversation |
| `/create_post` | Start the marketing post creation workflow |
| `/clear` | Reset conversation history |
| `/help` | Display available commands |
| `/cancel` | Cancel ongoing post creation |

## 🏗️ Project Structure

```
artisan-marketing-bot/
├── main.py              # Main bot application and webhook setup
├── create_post.py       # Post creation conversation handler
├── gemini.py           # Gemini AI integration and image/caption generation
├── tools.py            # Function declarations for structured output
├── utils.py            # Utility functions (message splitting)
├── setup_logging.py    # Logging configuration
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── tmp/               # Temporary file storage
│   ├── received/      # Uploaded images
│   └── generated/     # Generated marketing images
└── logs/              # Application logs
    └── bot.log
```

## 🔧 Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `GEMINI_API_KEY`: Your Google Gemini API key
- `BOT_USERNAME`: Your bot's username (without @)
- `WEBHOOK_URL`: Webhook URL for production deployment

### Gemini AI Setup

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Enable the Gemini 2.5 Flash model
4. Add the API key to your `.env` file

## 🤝 Usage Examples

### Creating a Marketing Post

1. Send `/create_post` to start
2. Upload a product image
3. Provide description:
   ```
   Clay Vase - Target audience: Home decorators - Style: Elegant, warm tone - Purpose: Social media post
   ```
4. Navigate through generated images using << >> buttons
5. Select your preferred image
6. Choose from 3 generated captions
7. Receive final marketing post

### Chat Interaction

Simply send messages to the bot for:
- Marketing advice
- Product description help
- Social media strategy
- General craftsmanship guidance

## 🎯 Target Audience

This bot is specifically designed for:
- Indian artisans and craftsmen
- Small business owners selling handmade products
- Creators looking to improve their social media presence
- Anyone wanting to showcase traditional Indian crafts

## 🛡️ Error Handling

The bot includes comprehensive error handling for:
- Invalid image uploads
- API failures
- Network timeouts
- User data persistence
- Conversation state management

## 📊 Logging

All bot activities are logged to:
- Console output for development
- `logs/bot.log` file for production monitoring

## 🔒 Privacy & Security

- Temporary files are stored locally and can be cleaned up regularly
- User conversations are not permanently stored
- API keys are kept secure through environment variables
- No personal data is transmitted to external services beyond what's necessary

## 🚀 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful image generation and text processing
- Telegram Bot API for seamless messaging integration
- The Indian artisan community for inspiration

## 📞 Support

If you encounter any issues or need help:

1. Check the logs in `logs/bot.log`
2. Ensure all environment variables are set correctly
3. Verify API keys are valid and have proper permissions
4. Create an issue on GitHub with detailed error information

---

**Made with ❤️ to support Indian artisans and their digital journey by team Gravity(Ashiq Sudheer,Mathew Thomas,Malay Kumar)**

📄 License
This project is licensed under the MIT License.
