import GeographicalRegions from './visualisations/geographicalRegions';
import GeographicalHeatmap from './visualisations/geographicalHeatMap';
import ReviewStats from './visualisations/reviewStats';
import './App.css';

function App() {
  return (
    <div className="App">
      {/* <GeographicalRegions /> <hr />
      <GeographicalHeatmap /> <hr /> */}
      <ReviewStats />
    </div>
  );
}

export default App;
