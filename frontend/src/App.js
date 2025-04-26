import GeographicalRegions from './visualisations/geographicalRegions';
import GeographicalHeatmap from './visualisations/geographicalHeatMap';
import './App.css';

function App() {
  return (
    <div className="App">
      <GeographicalRegions />
      <GeographicalHeatmap />
    </div>
  );
}

export default App;
