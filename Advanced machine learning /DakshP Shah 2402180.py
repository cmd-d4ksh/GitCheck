import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Load and encode dataset
data = pd.read_csv("mushrooms.csv")

le = LabelEncoder()
for col in data.columns:
    data[col] = le.fit_transform(data[col])

X = data.drop("class", axis=1)
y = data["class"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# 1A. Gradient Boost Classifier with GridSearchCV

gb = GradientBoostingClassifier(max_depth=3, random_state=42)

param_grid = {
    "n_estimators": [50, 100, 200],
    "learning_rate": [0.01, 0.1, 0.5],
    "subsample": [0.6, 0.8, 1.0]
}

grid_search = GridSearchCV(gb, param_grid=param_grid, cv=3, n_jobs=-1)
grid_search.fit(X_train, y_train)

print("Best Parameters:", grid_search.best_params_)

best_gb = grid_search.best_estimator_
y_pred = best_gb.predict(X_test)

print("Accuracy (Full Model):", accuracy_score(y_test, y_pred))


# 1B. Feature Importance + Rebuild with Top 3 Features



importances = best_gb.feature_importances_
feature_names = X.columns

plt.figure(figsize=(12, 6))
plt.bar(feature_names, importances)
plt.xticks(rotation=90)
plt.xlabel("Features")
plt.ylabel("Importance")
plt.title("Gradient Boost (Mushrooms Dataset)")
plt.tight_layout()
plt.savefig("feature_importance.png")
plt.close()
print("Graph saved as 'feature_importance.png'")

# Top 3 features
top3 = pd.Series(importances, index=feature_names).nlargest(3)
print("\nTop 3 Features:", top3.index.tolist())
X_top3 = data[top3.index]
X_train3, X_test3, y_train3, y_test3 = train_test_split(X_top3, y, test_size=0.2, random_state=42)

gb_top3 = GradientBoostingClassifier(max_depth=3,n_estimators=grid_search.best_params_["n_estimators"],learning_rate=grid_search.best_params_["learning_rate"],subsample=grid_search.best_params_["subsample"],random_state=42)
gb_top3.fit(X_train3, y_train3)

y_pred3 = gb_top3.predict(X_test3)

print("\nModel Performance with Top 3 Features:")
print("Accuracy:", accuracy_score(y_test3, y_pred3))
print("Precision:", precision_score(y_test3, y_pred3))
print("Recall:", recall_score(y_test3, y_pred3))
print("F1 Score:", f1_score(y_test3, y_pred3))

# Comment on performance:
# The mushroom dataset has 22 features, but only a few like odor, spore-print-color, gill-color tend to dominate feature importance. 
# Using just the top 3 features simplifies the model significantly. 
# If accuracy remains high more than 90% it confirms these features alone are strong predictors of edibility. A slight drop is expected


# 2A Multinomial Naive Bayes with TF-IDF on Spam Dataset

data_spam = pd.read_csv("spam.csv")
X_spam = data_spam["Message"]
y_spam = data_spam["Category"]


X_train_spam, X_test_spam, y_train_spam, y_test_spam = train_test_split(X_spam, y_spam, test_size=0.2, random_state=42)
tfidf = TfidfVectorizer()
X_train_spam_tfidf = tfidf.fit_transform(X_train_spam)
X_test_spam_tfidf = tfidf.transform(X_test_spam)


mnb = MultinomialNB()
mnb.fit(X_train_spam_tfidf, y_train_spam)

y_pred_spam = mnb.predict(X_test_spam_tfidf)
print("Multinomial Naive Bayes Performance on Spam Dataset:")
print("Accuracy:", accuracy_score(y_test_spam, y_pred_spam))
print("F1 Score:", f1_score(y_test_spam, y_pred_spam, average='weighted'))


# 2B Identify 5 Misclassified Messages from Test Set

results = pd.DataFrame({"Message": X_test_spam.values,"Actual": y_test_spam.values, "Predicted": y_pred_spam})

misclassified = results[results["Actual"] != results["Predicted"]].head(5)

print("\n5 Misclassified Messages:\n")
for i, row in misclassified.iterrows():
    print(f"Message   : {row['Message']}")
    print(f"Actual    : {row['Actual']}")
    print(f"Predicted : {row['Predicted']}")
    print("-" * 60)

# Why were these messages misclassified?
#these messages likely contain ambiguous language or features that overlap between spam and ham categories so that's why the model may have struggled to classify them correctly

#2C Predict Category for New Message with the TF-IDF value of 'free'

print("\n--- Section 2C: Message Prediction ---")
new_message = ["Congratulations! You have won a free vacation. Click the link to claim your prize now."]
new_message_tfidf = tfidf.transform(new_message)
prediction = mnb.predict(new_message_tfidf)
print("Prediction for new message:")
print(f"Message: {new_message[0]}")
print(f"Predicted Category: {prediction[0]}")
free_index = tfidf.vocabulary_.get('free')
if free_index is not None:
    free_tfidf_value = new_message_tfidf[0, free_index]
    print(f"TF-IDF value for 'free': {free_tfidf_value:.4f}")
else:
    print("The word 'free' is not in the TF-IDF vocabulary.")




