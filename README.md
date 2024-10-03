# Smart Fridge Project

## Setup

1. Clone the repository
2. Install requirements: `pip install -r requirements.txt`
3. Set up your environment variables:
   - Create a `.env` file in the root directory
   - Add your Spoonacular API key: `SPOONACULAR_API_KEY=your_key_here`
   - Add your database URL: `DATABASE_URL=your_database_url_here`
   - Add a secret key: `SECRET_KEY=your_secret_key_here`

   Alternatively, you can set these as environment variables in your system.

4. Run the application: `python main.py`

If you don't set up the API key in advance, the application will prompt you to enter it when making API calls.

## For Deployment

When deploying the application, make sure to set the following environment variables:
- SPOONACULAR_API_KEY
- DATABASE_URL
- SECRET_KEY

The method for setting these will depend on your hosting platform. Consult your platform's documentation for instructions on setting environment variables.