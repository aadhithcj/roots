import React, { useState, useCallback, useEffect, useRef } from "react";
import {
  Search,
  Leaf,
  Thermometer,
  Droplets,
  Cloud,
  Info,
  Loader2,
  RefreshCw,
  Zap,
  Navigation,
  Clock,
  TrendingUp,
  BarChart3,
  Play,
  X,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// --- INTERFACES ---
interface WeatherData {
  temperature: number;
  humidity: number;
  rainfall: number;
}
interface SoilData {
  nitrogen: string;
  phosphorus: string;
  potassium: string;
  ph: string;
}
interface CropRecommendation {
  name: string;
  confidence: number;
  description: string;
  trend: "up" | "down" | "stable";
  historicalData: number[];
}
interface LocationSuggestion {
  name: string;
  region: string;
  coordinates: { lat: number; lng: number };
}

// --- UI COMPONENTS ---
const AnimatedThermometer = () => ( <div className="relative w-8 h-8"> <Thermometer className="w-8 h-8 text-orange-400" /> <div className="absolute inset-0 animate-pulse bg-orange-400/20 rounded-full"></div> </div> );
const AnimatedDroplets = () => ( <div className="relative w-8 h-8"> <Droplets className="w-8 h-8 text-blue-400" /> <div className="absolute top-0 left-1/2 transform -translate-x-1/2"> <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce delay-100"></div> </div> </div> );
const AnimatedCloud = () => ( <div className="relative w-8 h-8"> <Cloud className="w-8 h-8 text-cyan-400" /> <div className="absolute inset-0 animate-pulse bg-cyan-400/10 rounded-full"></div> </div> );
const WeatherSkeleton = () => ( <div className="grid grid-cols-1 md:grid-cols-3 gap-6"> {[1, 2, 3].map((i) => ( <Card key={i} className="shadow-xl border-border bg-card/50 backdrop-blur-sm rounded-[40px]"> <CardContent className="p-8 text-center"> <div className="w-16 h-16 bg-muted/30 rounded-2xl mx-auto mb-4 animate-pulse"></div> <div className="h-4 bg-muted/30 rounded-full mb-2 animate-pulse"></div> <div className="h-8 bg-muted/30 rounded-full animate-pulse"></div> </CardContent> </Card> ))} </div> );
const ProgressIndicator = ({ currentStep }: { currentStep: number }) => { const steps = ["Location", "Weather", "Soil", "Crops"]; return ( <div className="flex items-center justify-center space-x-4 mb-8"> {steps.map((step, index) => ( <div key={step} className="flex items-center"> <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${ index < currentStep ? "bg-agro-green text-agro-dark" : index === currentStep ? "bg-agro-green/20 text-agro-green border-2 border-agro-green" : "bg-muted text-muted-foreground" }`}> {index + 1} </div> <span className={`ml-2 text-sm font-medium transition-colors ${ index <= currentStep ? "text-foreground" : "text-muted-foreground" }`}> {step} </span> {index < steps.length - 1 && ( <ChevronRight className="w-4 h-4 text-muted-foreground ml-4" /> )} </div> ))} </div> );};
const TutorialOverlay = ({ isVisible, onClose,}: { isVisible: boolean; onClose: () => void;}) => { if (!isVisible) return null; return ( <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"> <Card className="max-w-md bg-card border-border rounded-[40px] overflow-hidden"> <CardHeader className="bg-agro-green/10 border-b border-agro-green/20"> <div className="flex items-center justify-between"> <CardTitle className="flex items-center space-x-2"> <Sparkles className="w-5 h-5 text-agro-green" /> <span>Welcome to Roots!</span> </CardTitle> <Button variant="ghost" size="sm" onClick={onClose}> <X className="w-4 h-4" /> </Button> </div> </CardHeader> <CardContent className="p-6"> <p className="text-muted-foreground mb-4"> Get smart crop recommendations in 4 easy steps: </p> <ol className="space-y-2 text-sm"> <li className="flex items-center space-x-2"> <span className="w-5 h-5 bg-agro-green text-agro-dark rounded-full flex items-center justify-center text-xs font-bold"> 1 </span> <span>Search for your location</span> </li> <li className="flex items-center space-x-2"> <span className="w-5 h-5 bg-agro-green text-agro-dark rounded-full flex items-center justify-center text-xs font-bold"> 2 </span> <span>View weather conditions</span> </li> <li className="flex items-center space-x-2"> <span className="w-5 h-5 bg-agro-green text-agro-dark rounded-full flex items-center justify-center text-xs font-bold"> 3 </span> <span>Enter soil nutrient data</span> </li> <li className="flex items-center space-x-2"> <span className="w-5 h-5 bg-agro-green text-agro-dark rounded-full flex items-center justify-center text-xs font-bold"> 4 </span> <span>Get AI-powered crop recommendations</span> </li> </ol> <Button onClick={onClose} className="w-full mt-6 bg-agro-green hover:bg-agro-green-dark text-agro-dark rounded-3xl" > <Play className="w-4 h-4 mr-2" /> Get Started </Button> </CardContent> </Card> </div> );};
const ConfidenceMeter = ({ confidence, trend,}: { confidence: number; trend: "up" | "down" | "stable";}) => ( <div className="space-y-2"> <div className="flex justify-between text-xs text-muted-foreground"> <span>Confidence Score</span> <div className="flex items-center space-x-1"> <span className="font-semibold">{confidence}%</span> {trend === "up" && <TrendingUp className="w-3 h-3 text-green-400" />} {trend === "down" && ( <TrendingUp className="w-3 h-3 text-red-400 rotate-180" /> )} {trend === "stable" && ( <BarChart3 className="w-3 h-3 text-yellow-400" /> )} </div> </div> <div className="w-full bg-secondary rounded-full h-3 overflow-hidden relative"> <div className="h-3 rounded-full transition-all duration-1000 ease-out bg-gradient-to-r from-agro-green to-agro-green-light relative" style={{ width: `${confidence}%` }} > <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div> </div> </div> </div>);


export default function Index() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number;
    lng: number;
    name?: string;
  } | null>(null);
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [soilData, setSoilData] = useState<SoilData>({
    nitrogen: "",
    phosphorus: "",
    potassium: "",
    ph: "",
  });
  const [cropRecommendations, setCropRecommendations] = useState<
    CropRecommendation[]
  >([]);
  const [isLoadingWeather, setIsLoadingWeather] = useState(false);
  const [isLoadingCrops, setIsLoadingCrops] = useState(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);
  const [locationHistory, setLocationHistory] = useState<string[]>([]);
  const [currentStep, setCurrentStep] = useState(0);

  const searchInputRef = useRef<HTMLInputElement>(null);

  const locationSuggestions: LocationSuggestion[] = [ { name: "Punjab", region: "India's Granary", coordinates: { lat: 31.1471, lng: 75.3412 }, }, { name: "Haryana", region: "Green Revolution Hub", coordinates: { lat: 29.0588, lng: 76.0856 }, }, { name: "Uttar Pradesh", region: "Largest Agricultural State", coordinates: { lat: 26.8467, lng: 80.9462 }, }, { name: "West Bengal", region: "Rice Bowl of India", coordinates: { lat: 22.9868, lng: 87.855 }, }, { name: "Andhra Pradesh", region: "Spice Coast", coordinates: { lat: 15.9129, lng: 79.74 }, }, { name: "Karnataka", region: "Coffee & Cotton Belt", coordinates: { lat: 15.3173, lng: 75.7139 }, }, ];

  // --- Keyboard shortcuts ---
  useEffect(() => { const handleKeyboard = (e: KeyboardEvent) => { if (e.key === " " && e.ctrlKey) { e.preventDefault(); searchInputRef.current?.focus(); } if (e.key === "Enter" && e.ctrlKey) { e.preventDefault(); handleSearch(); } if (e.key === "?" && e.ctrlKey) { e.preventDefault(); setShowTutorial(true); } }; window.addEventListener("keydown", handleKeyboard); return () => window.removeEventListener("keydown", handleKeyboard); }, [searchQuery]);
  
  // --- Tutorial and History Logic ---
  useEffect(() => { const hasSeenTutorial = localStorage.getItem("agro-scout-tutorial"); if (!hasSeenTutorial) { setShowTutorial(true); localStorage.setItem("agro-scout-tutorial", "true"); } const history = localStorage.getItem("agro-scout-history"); if (history) { setLocationHistory(JSON.parse(history)); } }, []);


  // --- API CONNECTION LOGIC ---
  const API_BASE_URL = import.meta.env.VITE_API_URL;
  const fetchWeatherData = async (lat: number, lng: number) => {
    setIsLoadingWeather(true);
    setWeatherError(null);
    setCurrentStep(1);
    console.log(`Fetching weather for: Lat: ${lat}, Lng: ${lng}`);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/weather?lat=${lat}&lon=${lng}`
      );
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data: WeatherData = await response.json();
      console.log("Weather data received:", data);
      setWeatherData(data);
      setCurrentStep(2);
    } catch (error) {
      console.error("Fetch weather error:", error);
      setWeatherError("Failed to fetch weather data. Please try again.");
    } finally {
      setIsLoadingWeather(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    console.log(`Searching for: ${searchQuery}`);

    try {
        const geoResponse = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(searchQuery)}&count=1`);
        const geoData = await geoResponse.json();

        if (!geoData.results || geoData.results.length === 0) {
            throw new Error("Location not found.");
        }
        
        const { latitude, longitude, name } = geoData.results[0];
        console.log(`Location found: ${name} at ${latitude}, ${longitude}`);

        setSelectedLocation({ lat: latitude, lng: longitude, name: name });
        setCurrentStep(1);

        const newHistory = [ searchQuery, ...locationHistory.filter((h) => h !== searchQuery), ].slice(0, 5);
        setLocationHistory(newHistory);
        localStorage.setItem("agro-scout-history", JSON.stringify(newHistory));

        fetchWeatherData(latitude, longitude);

    } catch (error) {
        console.error("Geocoding error:", error);
        alert("Could not find the specified location. Please try another name.");
    }
  };

  const autoFetchSoilData = async () => {
    if (!selectedLocation || !selectedLocation.name) return;
    console.log(`Auto-fetching soil for: ${selectedLocation.name}`);

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/soil?location=${encodeURIComponent(
                selectedLocation.name
            )}`
        );
        if (!response.ok) {
            throw new Error("Failed to fetch soil data for the region.");
        }
        const data = await response.json();
        console.log("Soil data received:", data);
        setSoilData({
            nitrogen: String(data.nitrogen || ""),
            phosphorus: String(data.phosphorus || ""),
            potassium: String(data.potassium || ""),
            ph: String(data.ph || ""),
        });
        setCurrentStep(3);
    } catch (error) {
        console.error("Auto-fetch soil error:", error);
        alert("Could not auto-fetch soil data. Please enter values manually.");
    }
  };

  const recommendCrops = async () => {
    if (!selectedLocation || !weatherData) return;

    setIsLoadingCrops(true);
    setCurrentStep(3);

    const payload = {
        N: parseFloat(soilData.nitrogen),
        P: parseFloat(soilData.phosphorus),
        K: parseFloat(soilData.potassium),
        ph: parseFloat(soilData.ph),
        temperature: weatherData.temperature,
        humidity: weatherData.humidity,
        rainfall: weatherData.rainfall,
    };

    console.log("Sending payload for recommendation:", payload);

    try {
        const response = await fetch(`${API_BASE_URL}/api/recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to get recommendations");
        }

        const data = await response.json();
        console.log("Recommendations received:", data);
        setCropRecommendations(data.recommendations);
        setShowResults(true);
        setCurrentStep(4);
    } catch (error) {
        console.error("Error fetching crop recommendations:", error);
        alert(`An error occurred: ${error}`);
    } finally {
        setIsLoadingCrops(false);
    }
  };

  const handleLocationSuggestionClick = (suggestion: LocationSuggestion) => {
    setSearchQuery(suggestion.name);
    setSelectedLocation({ ...suggestion.coordinates, name: suggestion.name });
    setCurrentStep(1);
    fetchWeatherData(suggestion.coordinates.lat, suggestion.coordinates.lng);
  };
  
  const useCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setSelectedLocation({ lat: latitude, lng: longitude, name: "Current Location" });
          setSearchQuery("Current Location");
          setCurrentStep(1);
          fetchWeatherData(latitude, longitude);
        },
        (error) => console.error("Error getting location:", error),
      );
    }
  };
  
  const handleSoilInputChange = (field: keyof SoilData, value: string) => {
    setSoilData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-agro-dark relative">
      <TutorialOverlay
        isVisible={showTutorial}
        onClose={() => setShowTutorial(false)}
      />

      <header className="bg-card/50 backdrop-blur-xl border-b border-border sticky top-0 z-40">
        <div className="container mx-auto px-6 py-5">
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-agro-green rounded-2xl flex items-center justify-center shadow-lg transform transition-transform hover:scale-105">
                        <Leaf className="w-7 h-7 text-agro-dark" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-foreground">Roots</h1>
                        <p className="text-muted-foreground text-sm">Your farming companion</p>
                    </div>
                </div>
                <div className="flex items-center space-x-4">
                    <Button variant="ghost" size="sm" onClick={() => setShowTutorial(true)} className="text-muted-foreground hover:text-agro-green">
                        <Info className="w-4 h-4 mr-2" />
                        Help
                    </Button>
                    <p className="text-muted-foreground hidden md:block font-medium">Smart crop recommendations for modern farming</p>
                </div>
            </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12 space-y-12">
        <ProgressIndicator currentStep={currentStep} />
        
        <section className="relative">
           <Card className="overflow-hidden shadow-2xl border-border bg-card/50 backdrop-blur-sm rounded-[40px] transform transition-all duration-300 hover:shadow-3xl hover:scale-[1.01]">
            <CardHeader className="bg-agro-green/10 border-b border-agro-green/20">
              <CardTitle className="flex items-center space-x-3 text-xl">
                <Search className="w-6 h-6 text-agro-green" />
                <span className="text-foreground">Select Your Location</span>
              </CardTitle>
              <p className="text-muted-foreground">
                Search for any location to get started with crop analysis
              </p>
            </CardHeader>
            <CardContent className="p-8">
              <div className="flex space-x-4 mb-6">
                <div className="flex-1 relative">
                  <Input
                    ref={searchInputRef}
                    placeholder="Search for a location... (Ctrl+Space)"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                    className="h-14 text-lg border-border bg-secondary/50 focus:border-agro-green focus:ring-agro-green/20 focus:ring-4 rounded-3xl transition-all duration-300 focus:shadow-lg focus:shadow-agro-green/20"
                  />
                  {searchQuery && (
                    <Button variant="ghost" size="sm" onClick={() => setSearchQuery("")} className="absolute right-2 top-1/2 transform -translate-y-1/2 hover:bg-muted/50 rounded-full">
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
                <Button onClick={handleSearch} disabled={!searchQuery.trim()} className="bg-agro-green hover:bg-agro-green-dark text-agro-dark px-8 h-14 text-lg font-semibold rounded-3xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-95">
                  <Search className="w-5 h-5 mr-2" />
                  Search
                </Button>
              </div>

              <div className="flex flex-wrap gap-3 mb-6">
                <Button onClick={useCurrentLocation} variant="outline" size="sm" className="border-agro-green/50 text-agro-green hover:bg-agro-green hover:text-white rounded-3xl transform transition-all hover:scale-105">
                  <Navigation className="w-4 h-4 mr-2" />
                  Use Current Location
                </Button>

                {locationHistory.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Recent:</span>
                    {locationHistory.slice(0, 3).map((location, index) => (
                      <Button key={index} onClick={() => { setSearchQuery(location); handleSearch(); }} variant="ghost" size="sm" className="text-xs hover:bg-agro-green/10 hover:text-agro-green rounded-2xl">
                        {location}
                      </Button>
                    ))}
                  </div>
                )}
              </div>

              <div className="mb-8">
                <p className="text-sm font-medium text-foreground mb-3">
                  Popular Farming Regions:
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {locationSuggestions.map((suggestion, index) => (
                    <button key={index} onClick={() => handleLocationSuggestionClick(suggestion)} className="p-3 text-left border border-border bg-secondary/30 hover:bg-secondary/50 rounded-2xl transition-all duration-300 hover:shadow-md hover:scale-105 group">
                      <div className="font-medium text-foreground group-hover:text-agro-green transition-colors">{suggestion.name}</div>
                      <div className="text-xs text-muted-foreground">{suggestion.region}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* ## MAP SECTION REMOVED ## */}

            </CardContent>
          </Card>
        </section>

        {selectedLocation && (
          <section className="animate-in fade-in-50 duration-500">
            {isLoadingWeather ? (
              <WeatherSkeleton />
            ) : weatherError ? (
              <Card className="border-red-500/20 bg-red-500/10 rounded-[40px]">
                <CardContent className="p-6 flex items-center justify-between">
                  <span className="text-red-400 font-medium">{weatherError}</span>
                  <Button onClick={() => selectedLocation && fetchWeatherData(selectedLocation.lat, selectedLocation.lng)} variant="outline" size="sm" className="border-red-500/30 text-red-400 hover:bg-red-500/20 rounded-3xl">
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Retry
                  </Button>
                </CardContent>
              </Card>
            ) : (
              weatherData && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Card className="shadow-xl border-border bg-card/50 backdrop-blur-sm hover:shadow-2xl transition-all duration-300 hover:scale-105 rounded-[40px]">
                    <CardContent className="p-8 text-center">
                      <div className="w-16 h-16 bg-orange-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4"><AnimatedThermometer /></div>
                      <h3 className="font-semibold text-foreground mb-2 text-lg">Temperature</h3>
                      <p className="text-3xl font-bold text-orange-400">{weatherData.temperature}°C</p>
                    </CardContent>
                  </Card>
                  <Card className="shadow-xl border-border bg-card/50 backdrop-blur-sm hover:shadow-2xl transition-all duration-300 hover:scale-105 rounded-[40px]">
                    <CardContent className="p-8 text-center">
                      <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4"><AnimatedDroplets /></div>
                      <h3 className="font-semibold text-foreground mb-2 text-lg">Humidity</h3>
                      <p className="text-3xl font-bold text-blue-400">{weatherData.humidity}%</p>
                    </CardContent>
                  </Card>
                  <Card className="shadow-xl border-border bg-card/50 backdrop-blur-sm hover:shadow-2xl transition-all duration-300 hover:scale-105 rounded-[40px]">
                    <CardContent className="p-8 text-center">
                      <div className="w-16 h-16 bg-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4"><AnimatedCloud /></div>
                      <h3 className="font-semibold text-foreground mb-2 text-lg">Rainfall</h3>
                      <p className="text-3xl font-bold text-cyan-400">{weatherData.rainfall}mm</p>
                    </CardContent>
                  </Card>
                </div>
              )
            )}
          </section>
        )}

        {weatherData && (
          <section className="animate-in fade-in-50 duration-700">
            <Card className="shadow-2xl border-border bg-card/50 backdrop-blur-sm rounded-[40px] transform transition-all duration-300 hover:shadow-3xl">
              <CardHeader className="bg-agro-green/10 border-b border-agro-green/20">
                <CardTitle className="text-foreground text-xl">Soil Analysis</CardTitle>
                <p className="text-muted-foreground">Enter your soil nutrient levels for accurate crop recommendations</p>
              </CardHeader>
              <CardContent className="p-8">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  {[
                    { key: "nitrogen", label: "Nitrogen (N)", placeholder: "0-200", info: "Essential for leaf growth", },
                    { key: "phosphorus", label: "Phosphorus (P)", placeholder: "0-100", info: "Important for root development", },
                    { key: "potassium", label: "Potassium (K)", placeholder: "0-300", info: "Helps with disease resistance", },
                    { key: "ph", label: "pH Level", placeholder: "3.0-10.0", info: "Soil acidity/alkalinity", },
                  ].map((field) => (
                    <div key={field.key} className="space-y-3 group">
                      <label className="text-sm font-semibold text-foreground flex items-center">
                        {field.label}
                        <div className="relative ml-2">
                          <Info className="w-4 h-4 text-muted-foreground" />
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">{field.info}</div>
                        </div>
                      </label>
                      <Input placeholder={field.placeholder} value={soilData[field.key as keyof SoilData]} onChange={(e) => handleSoilInputChange(field.key as keyof SoilData, e.target.value)} className="h-12 border-border bg-secondary/50 focus:border-agro-green focus:ring-agro-green/20 focus:ring-4 rounded-3xl transition-all duration-300 focus:shadow-lg" type="number" />
                    </div>
                  ))}
                </div>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Button onClick={autoFetchSoilData} variant="outline" className="border-agro-green/50 text-agro-green hover:bg-agro-green hover:text-white h-12 px-6 rounded-3xl font-semibold transform transition-all hover:scale-105">
                    <Zap className="w-4 h-4 mr-2" />
                    Auto-fetch soil data
                  </Button>
                  <Button onClick={recommendCrops} disabled={ isLoadingCrops || !soilData.nitrogen || !soilData.phosphorus || !soilData.potassium || !soilData.ph } className="bg-agro-green hover:bg-agro-green-dark text-agro-dark px-8 h-12 text-lg font-semibold flex-1 sm:flex-none rounded-3xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-95">
                    {isLoadingCrops ? ( <> <Loader2 className="w-5 h-5 mr-2 animate-spin" /> Analyzing... </> ) : ( <> <Sparkles className="w-5 h-5 mr-2" /> Recommend Crops </> )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>
        )}

        {showResults && cropRecommendations.length > 0 && (
          <section className="animate-in fade-in-50 duration-900">
            <Card className="shadow-2xl border-border bg-card/50 backdrop-blur-sm rounded-[40px]">
              <CardHeader className="bg-agro-green/10 border-b border-agro-green/20">
                <CardTitle className="text-foreground text-xl">Recommended Crops</CardTitle>
                <p className="text-muted-foreground">AI-powered recommendations based on your location, weather, and soil conditions</p>
              </CardHeader>
              <CardContent className="p-8">
                <div className="space-y-6">
                  {cropRecommendations.map((crop, index) => (
                    <div key={crop.name} className="flex items-center justify-between p-6 rounded-3xl border border-border bg-secondary/30 hover:bg-secondary/50 hover:shadow-lg transition-all duration-300 transform hover:scale-[1.02] group">
                      <div className="flex-1">
                        <div className="flex items-center space-x-4 mb-3">
                          <h3 className="font-bold text-foreground text-lg group-hover:text-agro-green transition-colors">{crop.name}</h3>
                          <Badge className="bg-agro-green/20 text-agro-green border-agro-green/30 px-3 py-1 rounded-full font-semibold">{crop.confidence}% match</Badge>
                          <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                            <BarChart3 className="w-3 h-3" />
                            <span>Historical: {crop.historicalData.join("% → ")}%</span>
                          </div>
                        </div>
                        <p className="text-muted-foreground mb-4">{crop.description}</p>
                        <ConfidenceMeter confidence={crop.confidence} trend={crop.trend} />
                      </div>
                      <Button variant="outline" size="sm" className="ml-6 border-agro-green/50 text-agro-green hover:bg-agro-green hover:text-white rounded-3xl px-6 font-semibold transform transition-all hover:scale-105">
                        Learn more
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </section>
        )}
      </main>

      <div className="fixed bottom-4 right-4 text-xs text-muted-foreground bg-card/50 backdrop-blur-sm border border-border rounded-2xl p-3">
        <div>Ctrl+Space: Focus search</div>
        <div>Ctrl+Enter: Search</div>
        <div>Ctrl+?: Help</div>
      </div>
    </div>
  );
}