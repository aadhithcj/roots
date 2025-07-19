# Roots: AI-Powered Crop Recommendation System
**[🔗 Roots](rootssss.netlify.app/ )** 


---



## Abstract



Modern agriculture faces the persistent challenge of optimizing crop selection to maximize yield and ensure sustainability against a backdrop of varying climatic and soil conditions. This project, "Roots," presents a machine learning powered web application designed to simplify this complexity by providing farmers with crop predictions

The core of the system is a **Random Forest Classifier**, trained on a comprehensive agricultural dataset. The model accurately predicts optimal crops based on seven key environmental parameters: soil Nitrogen (N), Phosphorus (P), and Potassium (K) levels, soil pH, temperature, humidity, and annual rainfall.



To deliver these insights, the project is architected as a modern fullstack application. The backend is a lightweight **Flask API** that serves the trained scikit-learn model, exposing an endpoint to process environmental data and return the top three crop recommendations. A key feature of the backend is its integration with the **OpenMeteo API**, which fetches both live weather data (temperature, humidity) and calculates a 30 day average annual rainfall for any given location, ensuring the data aligns with the model's training.



The frontend is a highly interactive and responsive single page application built with **React** and styled with **Tailwind CSS**. It provides a streamlined user experience, allowing users to get recommendations by searching for a location or using their device's geolocation. Frontend is hosted on Netify and backend is hosted on Render. By integrating a robust machine learning model with live and historical environmental data services, Roots provides a practical and accessible tool for modern farming, aiming to help those in need of crop recommendations.



---

## Note

The first request will be slow as waking up Render backend initially takes a few seconds.



## Screenshots



*UI Preview*

### Screenshots

![Showcase](<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/fd1e8014-e6d6-4887-8f11-77942582513c" />)

![Landing page](<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/395c067d-7ebd-48fe-88b0-8beebc0b66d0" />)

**Weather and Soil Input**
![Location](<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/54d412ad-a259-46bd-9540-c2d2814e4198" />)

**Weather and Soil Input**
![Values and prediction](<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/af6213a4-0878-4ed3-ae4a-520c5170783a" />)

---



## Model Training



The machine learning model for this project was trained and evaluated in a Google Colab notebook. You can view the complete data analysis, model training, and evaluation process here:



**[My Collab Link](https://colab.research.google.com/drive/1rRuLAL7JmfPHX_4VJgnyz2bjmBmZcpVS?usp=sharing)**
