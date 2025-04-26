import React, { useEffect, useState, useRef } from 'react';
import { getGeographicalData } from '../apiService';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';

const GeographicalHeatmap = () => {
  const [centres, setCentres] = useState([]);
  const [error, setError] = useState(null);
  const mapRef = useRef(null); // Create a reference for the map instance

  // Fetch the geographical data from your API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getGeographicalData();
        setCentres(response.data);
      } catch (error) {
        setError('Error fetching geographical data');
        console.error("Error fetching geographical data:", error);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (centres.length > 0 && !mapRef.current) { // Only create the map once
      const map = L.map('heatmap', {
        center: [1.3521, 103.8198], // Center of Singapore (adjust as needed)
        zoom: 12,
        zoomControl: true
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      // Prepare the data for the heatmap
      const heatmapData = centres.map(centre => [
        parseFloat(centre.latitude),  // Latitude
        parseFloat(centre.longitude), // Longitude
        centre.avg_rating // Weight (avg_rating)
      ]);

      // Create the heatmap
      L.heatLayer(heatmapData, {
        radius: 25,
        blur: 15,
        maxZoom: 17,
      }).addTo(map);

      mapRef.current = map; // Store the map instance
    }

    // Cleanup: Destroy the map when the component unmounts
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [centres]); // Only re-run when `centres` changes

  if (error) {
    return (
      <div>
        <h2>{error}</h2>
      </div>
    );
  }

  return (
    <div>
      <h2>Hawker Centres Heatmap</h2>
      <div id="heatmap" style={{ height: "800px", width: "100%" }}></div>
    </div>
  );
};

export default GeographicalHeatmap;
