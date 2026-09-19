import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
df = pd.read_csv("products.csv")

# Remove $ from price column if present
df["price"] = (
    df["price"]
    .astype(str)
    .str.replace("$", "", regex=False)
)

# Replace missing values
df.fillna("", inplace=True)

# Create combined text
df["combined_text"] = (
    df["title"] + " " +
    df["description"] + " " +
    df["category"]
)

# TF-IDF
tfidf = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf.fit_transform(df["combined_text"])

# Cosine Similarity
cosine_sim = cosine_similarity(tfidf_matrix)

def recommend_products(product_id):

    try:
        idx = df[df["product_id"] == product_id].index[0]
    except:
        return []

    similarity_scores = list(enumerate(cosine_sim[idx]))

    similarity_scores = sorted(
        similarity_scores,
        key=lambda x: x[1],
        reverse=True
    )

    similarity_scores = similarity_scores[1:6]

    recommendations = []

    for i, score in similarity_scores:

        recommendations.append({
            "product_id": df.iloc[i]["product_id"],
            "title": df.iloc[i]["title"],
            "price": df.iloc[i]["price"],
            "category": df.iloc[i]["category"],
            "description": df.iloc[i]["description"],
            "image_url": df.iloc[i]["image_url"]
        })

    return recommendations