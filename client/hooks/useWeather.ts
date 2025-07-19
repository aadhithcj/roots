import { useState } from 'react';

// Get the API base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL;

// Define the structure of the weather data
interface WeatherData {
  temperature: number;
  humidity: number;
  rainfall: number;
}

export function useWeather() {
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWeatherData = async (lat: number, lng: number) => {
    setIsLoading(true);
    setError(null);
    console.log(`Fetching weather for: Lat: ${lat}, Lng: ${lng}`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/weather?lat=${lat}&lon=${lng}`);
      if (!response.ok) {
        throw new Error("Failed to fetch weather data from the server.");
      }
      const data: WeatherData = await response.json();
      setWeatherData(data);
      console.log("Weather data received:", data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred.";
      console.error("Fetch weather error:", errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return { weatherData, isLoading, error, fetchWeatherData };
}