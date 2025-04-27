import GeographicalRegions from './visualisations/geographicalRegions';
import GeographicalHeatmap from './visualisations/geographicalHeatMap';
import ReviewStats from './visualisations/reviewStats';
import CleaningGanttChart from './visualisations/cleaningSched';
import './App.css';

function App() {
  return (
    <div className="App">
      <CleaningGanttChart />
      <ReviewStats />
      <GeographicalRegions /> <hr />
      <GeographicalHeatmap /> <hr />
      <br />
      <br />
      <br />
    </div>
  );
}

export default App;
