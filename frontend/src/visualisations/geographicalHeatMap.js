import React, { useEffect, useState, useRef } from 'react';
import { getGeographicalData } from '../apiService';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';

const GeographicalHeatmap = () => {
  const [centres, setCentres] = useState([]);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('rating'); // 'rating' or 'stalls'
  const [showMarkers, setShowMarkers] = useState(true);
  const mapRef = useRef(null);
  const heatLayerRef = useRef(null); // for updating the heat layer
  const markerLayerRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getGeographicalData();
        setCentres(response.data);
      } catch (error) {
        setError('Error fetching geographical data');
        console.error('Error fetching geographical data:', error);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (centres.length > 0 && !mapRef.current) {
      const map = L.map('heatmap', {
        center: [1.3521, 103.8198],
        zoom: 12,
        zoomControl: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);

      mapRef.current = map;
    }

    if (centres.length > 0 && mapRef.current) {
      if (heatLayerRef.current) {
        heatLayerRef.current.remove(); // Remove existing heat layer
      }

      const maxValue = Math.max(
        ...centres.map(centre => 
          mode === 'rating'
            ? centre.avg_rating || 0
            : centre.stalls || 0
        )
      ) || 1;

      const minValue = Math.min(
        ...centres.map(centre => 
          mode === 'rating'
            ? centre.avg_rating || 0
            : centre.stalls || 0
        )
      ) || 0;

      const heatmapData = centres.map(centre => {
        const value = mode === 'rating' ? centre.avg_rating || 0 : centre.stalls || 0;
        return [
          parseFloat(centre.latitude),
          parseFloat(centre.longitude),
          (value - minValue) / (maxValue - value),
          ]
        }
      );
      
      console.log(heatmapData);

      heatLayerRef.current = L.heatLayer(heatmapData, {
        radius: 30,
        blur: 35,
        maxZoom: 17,
        max: 1,
        gradient: {
          0.0: 'blue',
          0.5: 'lime',
          0.75: 'orange',
          1.0: 'red',
        },
      }).addTo(mapRef.current);

      if (markerLayerRef.current) {
        markerLayerRef.current.clearLayers();
      } else {
        markerLayerRef.current = L.layerGroup().addTo(mapRef.current);
      }
      
      centres.forEach(centre => {
        const { latitude, longitude, name, avg_rating, stalls } = centre;
      
        if (latitude && longitude) {
          const marker = L.circleMarker([parseFloat(latitude), parseFloat(longitude)], {
            radius: 0.05,
            color: showMarkers? 'black':'transparent',
            weight: 1,
            fillOpacity: 0.5,
          });
      
          marker.bindTooltip(`
            <strong>${name}</strong><br/>
            Rating: ${avg_rating || 'N/A'}<br/>
            Number of Stalls: ${stalls || 'N/A'}
          `, { direction: 'top', offset: [0, -10] });
      
          marker.addTo(markerLayerRef.current);
        }
      });
      
    }

    return () => {
      if (mapRef.current && heatLayerRef.current) {
        heatLayerRef.current.remove();
      }
    };
  }, [centres, mode, showMarkers]);

  const handleModeChange = (newMode) => {
    setMode(newMode);
  };

  const handleToggleMarkers = () => {
    setShowMarkers(!showMarkers);
  };


  if (error) {
    return (
      <div>
        <h2>{error}</h2>
      </div>
    );
  }

  return (
    <div className="geographical-heatmap">
      <h2>Hawker Centres Heatmap Based on {mode === 'rating' ? 'Rating' : 'Number of Stalls'}</h2>

      <div style={{ marginBottom: '10px' }}>
        <button onClick={() => handleModeChange('rating')} disabled={mode === 'rating'}>
          Based on Rating
        </button>
        <button onClick={() => handleModeChange('stalls')} disabled={mode === 'stalls'} style={{ marginLeft: '10px' }}>
          Based on Number of Stalls
        </button>
      </div>

      <div id="heatmap" style={{ height: '500px', width: '100%' }}></div>

      <div style={{ marginTop: '10px', padding: '10px', backgroundColor: 'white', width: 'fit-content', borderRadius: '8px', boxShadow: '0 0 5px rgba(0,0,0,0.3)' }}>
        <strong>Legend:</strong>
        <div className="legend-item">
          <div style={{ width: '20px', height: '20px', backgroundColor: 'blue' }}></div>
          <span className='legend-margin'>Low</span>
        </div>
        <div className="legend-item">
          <div style={{ width: '20px', height: '20px', backgroundColor: 'lime' }}></div>
          <span className='legend-margin'>Medium</span>
        </div>
        <div className="legend-item">
          <div style={{ width: '20px', height: '20px', backgroundColor: 'orange' }}></div>
          <span className='legend-margin'>High</span>
        </div>
        <div className="legend-item">
          <div style={{ width: '20px', height: '20px', backgroundColor: 'red' }}></div>
          <span className='legend-margin'>Very High</span>
        </div>
        <input type="checkbox" checked={showMarkers} onChange={handleToggleMarkers} style={{ marginTop: '10px' }}></input>
        <label className='legend-margin'>Show Markers</label>
      </div>
    </div>
  );
};

export default GeographicalHeatmap;

