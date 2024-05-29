from flask import Flask, render_template, request
from flask_cors import CORS
from textblob import TextBlob
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

# Load JSON file
file_path = r'C:\Users\varua\Downloads\food-del\food-del\Flask\restaurant_details.json'
with open(file_path) as f:
    file = json.load(f)

# Extract required information
indexes = list(file.keys())
res_name, res_loc, res_category, reviews, res_rating = [], [], [], [], []

for k in range(len(indexes)):
    # Extract restaurant information
    res_name.append(file[indexes[k]]['title'] + ", " + file[indexes[k]]['address'])
    res_loc.append(file[indexes[k]]['location'][0].split("destination=")[1])
    res_category.append(file[indexes[k]]['category'])
    
    # Perform sentiment analysis on reviews using TextBlob
    data = [x.strip() for x in list(file[indexes[k]]['users_review'].values()) if len(x) >= 1]
    positive_reviews = sum(1 for review in data if TextBlob(review).sentiment.polarity > 0)
    reviews.append(positive_reviews)
    
    res_rating.append(file[indexes[k]]['dining_rating'])

# Create DataFrame
df = pd.DataFrame({
    'res_name': res_name,
    'res_loc': res_loc,
    'res_category': res_category,
    'positive_reviews': reviews,
    'res_rating': res_rating
})

# Calculate additional metrics
df['total_no_reviews'] = len(df)
df['actual_rating'] = round((((df['positive_reviews'] / df['total_no_reviews']) * 100) * 5) / 100, 1)

# Create bag of words representation
df['bag_of_words'] = [" ".join(x) for x in df['res_category']]
df = df.drop(['res_loc', 'res_category', 'total_no_reviews'], axis=1)
df['res_name'] = df['res_name'].apply(lambda x: x.split(',')[0])

# Calculate cosine similarity
tfidf = TfidfVectorizer()
tfidf_matrix = tfidf.fit_transform(df['bag_of_words'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Recommendation function
def recommendation(title, total_result=5, threshold=0.5):
    idx = df[df['res_name'] == title].index[0]
    df['similarity'] = cosine_sim[idx]
    sort_df = df.sort_values(by='similarity', ascending=False)[1:total_result+1]
    restaurants = sort_df['res_name']
    return restaurants.tolist()

ratings_dict = dict(zip(df['res_name'], df['res_rating']))
# Routes for rendering HTML templates
@app.route('/')
def home():
    sorted_ratings = dict(sorted(ratings_dict.items(), key=lambda item: item[1], reverse=True))
    return render_template('index.html', ratings=sorted_ratings)
    return send_from_directory('../frontend/build', 'index.html')

@app.route('/recommendation', methods=['POST'])
def get_recommendation():
    title = request.form['title']
    recommendations = recommendation(title)
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend/build/static', path)

if __name__ == '__main__':
    app.run(debug=True)
