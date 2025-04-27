import React, { useState, useEffect } from 'react';
import { getGeographicalData } from '../apiService';
import ReactApexChart from 'react-apexcharts';

const assignRegion = (lat, lon) => {
    const centralLat = 1.3521;
    const centralLon = 103.8198;
    const centralRadius = 0.02; // small threshold for 'central'

    if (Math.abs(lat - centralLat) <= centralRadius && Math.abs(lon - centralLon) <= centralRadius) {
            return 'Central';
    } else if (lat > centralLat + centralRadius) {
        if (lon > centralLon) return 'NE';
        else return 'NW';
    } else if (lat < centralLat - centralRadius) {
        if (lon > centralLon) return 'SE';
        else return 'SW';
    } else {
        if (lat > centralLat) return 'North';
        else return 'South';
    }
};


const GeographicalRegions = () => {

    const [centres, setCentres] = useState([]);
    const [withRegion, setWithRegion] = useState([]);
    const [selectedRegion, setSelectedRegion] = useState('North');

    useEffect(() => {
        const fetchData = async () => {
            try {
                    const response = await getGeographicalData();
                    setCentres(response.data);
            } catch (error) {
                console.error('Error fetching geographical data:', error);
            }
        };
        fetchData();
        }, []);
    
    useEffect(() => {
        if (centres.length > 0) {

    
            const enriched = centres.map(centre => {
                const lat = parseFloat(centre.latitude);
                const lon = parseFloat(centre.longitude);
                let region = '';
        
                region = assignRegion(lat, lon);
        
                return { ...centre, region };
            });
    
            setWithRegion(enriched);
        }
    }, [centres]);
    
    const regions = ['North', 'South', 'Central', 'NE', 'NW', 'SE', 'SW'];

    const calculateRegionStats = () => {
        const stats = [];
    
        regions.forEach(region => {
            const regionData = withRegion.filter(c => c.region === region);
    
            if (regionData.length > 0) {
                const best = regionData.reduce((prev, curr) => (curr.avg_rating > prev.avg_rating ? curr : prev));
                const worst = regionData.reduce((prev, curr) => (curr.avg_rating < prev.avg_rating ? curr : prev));
                const avgRating =
                    regionData.reduce((sum, centre) => sum + (centre.avg_rating || 0), 0) / regionData.length;
        
                stats.push({
                    region,
                    bestCentre: best.name,
                    bestAvgRating: best.avg_rating.toFixed(2),
                    worstCentre: worst.name,
                    worstAvgRating: worst.avg_rating.toFixed(2),
                    avgRegionRating: avgRating.toFixed(2),
                });
                } else {
                stats.push({
                    region,
                    bestCentre: '-',
                    bestAvgRating: '-',
                    worstCentre: '-',
                    worstAvgRating: '-',
                    avgRegionRating: '-',
                });
            }
        });
    
        return stats;
    };
    
    const regionStats = calculateRegionStats();


    const groupedOptions = {
        chart: {
            type: 'bar',
            height: 400,
            stacked: false
        },
        plotOptions: {
            bar: {
            horizontal: false,
            columnWidth: '55%',
            endingShape: 'rounded',
            }
        },
        dataLabels: {
            enabled: false
        },
        xaxis: {
            categories: regions, // ["North", "South", "Central", etc.]
            title: { text: 'Region' }
        },
        yaxis: {
            min: 0,
            max: 5,
            title: { text: 'Average Rating' }
        },
        title: {
            text: 'Hawker Centre Performance by Region',
            align: 'center'
        },
        tooltip: {
            y: {
            formatter: (val) => {
                if (val == null || isNaN(val)) return '-';
                return val.toFixed(2) + ' stars';
                }
            }
        }
        };
        
        const groupedSeries = [
        {
            name: 'Best Centre Rating',
            data: regionStats.map(r => r.bestAvgRating !== '-' ? parseFloat(r.bestAvgRating) : 0)
        },
        {
            name: 'Worst Centre Rating',
            data: regionStats.map(r => r.worstAvgRating !== '-' ? parseFloat(r.worstAvgRating) : 0)
        },
        {
            name: 'Average Region Rating',
            data: regionStats.map(r => r.avgRegionRating !== '-' ? parseFloat(r.avgRegionRating) : 0)
        }
    ];


    // region specific

    const getRegionSpecific = () => {
        const output = {};

        regions.forEach(region => {
            const regionData = withRegion.filter(c => c.region === region);
    
            if (regionData.length > 0) {
                const best = regionData.reduce((prev, curr) => (curr.avg_rating > prev.avg_rating ? curr : prev));
                const worst = regionData.reduce((prev, curr) => (curr.avg_rating < prev.avg_rating ? curr : prev));
                const avgRating =regionData.reduce((sum, centre) => sum + (centre.avg_rating || 0), 0) / regionData.length;

                const allStalls = regionData.flatMap(c => 
                    (c.top3_stalls || []).map(stall => ({
                        stallName: stall.stall_name,
                        rating: stall.rating,
                        centreName: c.name,
                    }))
                );
                
                const sortedStalls = allStalls.sort((a, b) => b.rating - a.rating);
                const overallTop3 = sortedStalls.slice(0, 3);
                console.log(overallTop3)

                output[region] = {
                    bestCentre: best.name,
                    bestAvgRating: best.avg_rating.toFixed(2),
                    top3Stalls: best.top3_stalls,
                    worstCentre: worst.name,
                    worstAvgRating: worst.avg_rating.toFixed(2),
                    avgRegionRating: avgRating.toFixed(2),
                    overallTop3: overallTop3
                };
            } else {
                output[region] = {
                    bestCentre: '-',
                    bestAvgRating: '-',
                    top3Stalls: '-',
                    worstCentre: '-',
                    worstAvgRating: '-',
                    avgRegionRating: '-',
                    overallTop3: '-'
                };
            }
        });
        
        return output;
    }
    
    const regionSpecific = getRegionSpecific();


    
    return (
        <div style={{ padding: '20px', width:'80%', margin:'auto'}}>
            <h2>Rating Distribution of Hawker Centres by Region</h2>
            <ReactApexChart options={groupedOptions} series={groupedSeries} type="bar" height={350} />


            <h2>Overall Hawker Centre Performance based on Region</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr style={{ backgroundColor: '#f0f0f0' }}>
                    <th style={{ border: '1px solid #ccc', padding: '8px', width:'10%' }}>Region</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px', width:'30%'}}>Best Hawker Centre</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px' }}>Best Hawker Centre Rating</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px', width:'30%' }}>Worst Hawker Centre</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px' }}>Worst Hawker Centre Rating</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px' }}>Region Avg Rating</th>
                    </tr>
                </thead>
                <tbody>
                    {regionStats.map((row, index) => (
                    <tr key={index}>
                        <td className='table-cell'>{row.region}</td>
                        <td className='table-cell'>{row.bestCentre}</td>
                        <td className='table-cell'>{row.bestAvgRating}⭐</td>
                        <td className='table-cell'>{row.worstCentre}</td>
                        <td className='table-cell'>{row.worstAvgRating}⭐</td>
                        <td className='table-cell'>{row.avgRegionRating}⭐</td>
                    </tr>
                    ))}
                </tbody>
            </table>

            <h2>Hawker Centre Performance for {selectedRegion}</h2>
            <select style={{marginBottom:"10px"}} value={selectedRegion} onChange={(e) => setSelectedRegion(e.target.value)}>
                {regions.map((region) => (
                    <option key={region} value={region}>
                    {region}
                    </option>
                ))}
            </select>

            <div>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <tbody>
                    <tr>
                        <td className='table-cell'>Best Hawker Centre in Region</td>
                        <td className='table-cell'>{regionSpecific[selectedRegion].bestCentre} ({regionSpecific[selectedRegion].bestAvgRating} ⭐)</td>
                    </tr>
                    <tr>
                        <td className='table-cell'>Worst Hawker Centre in Region</td>
                        <td className='table-cell'>{regionSpecific[selectedRegion].worstCentre} ({regionSpecific[selectedRegion].worstAvgRating} ⭐)</td>
                    </tr>
                    <tr>
                        <td className='table-cell'>Average Rating of Hawker Centres in Region</td>
                        <td className='table-cell'>{regionSpecific[selectedRegion].avgRegionRating} ⭐</td>
                    </tr>
                    <tr>
                        <td className='table-cell'>Top 3 Stalls Overall</td>
                        <td className='table-cell'>
                            {Array.isArray(regionSpecific[selectedRegion].overallTop3) ? (
                                <ul>
                                    {regionSpecific[selectedRegion].overallTop3.map((stall, index) => (
                                    <li key={index}>{stall.stallName}, {stall.centreName} - {stall.rating}</li>
                                    ))}
                                </ul>
                                ) : (
                                <p>-</p>
                            )}
                        </td>
                    </tr>
                    </tbody>
                </table>

                <br />

                <table style={{ width: '100%', borderCollapse: 'collapse'}}>
                    <thead>
                        <tr style={{ backgroundColor: '#f0f0f0' }}>
                        <th style={{ border: '1px solid #ccc', padding: '8px' }}>Top 3 Stalls in Best Hawker Centre in {selectedRegion} Region</th>
                        <th style={{ border: '1px solid #ccc', padding: '8px', width: '10%' }}>Rating</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Array.isArray(regionSpecific[selectedRegion].top3Stalls) ? (
                        regionSpecific[selectedRegion].top3Stalls.map((stall, index) => (
                            <tr key={index}>
                            <td className="table-cell">{stall.stall_name}</td>
                            <td className="table-cell">{stall.rating}</td>
                            </tr>
                        ))
                        ) : (
                        <tr>
                            <td className="table-cell">-</td>
                            <td className="table-cell">-</td>
                        </tr>
                        )}
                    </tbody>
                </table>
                <br />
                <table style={{ width: '100%', borderCollapse: 'collapse'}}>
                    <thead>
                        <tr style={{ backgroundColor: '#f0f0f0' }}>
                        <th style={{ border: '1px solid #ccc', padding: '8px', width: '45%' }}>Top 3 Stalls in {selectedRegion} Region</th>
                        <th style={{ border: '1px solid #ccc', padding: '8px' }}>Hawker Centre</th>
                        <th style={{ border: '1px solid #ccc', padding: '8px', width:'10%' }}>Rating</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Array.isArray(regionSpecific[selectedRegion].top3Stalls) ? (
                        regionSpecific[selectedRegion].overallTop3.map((stall, index) => (
                            <tr key={index}>
                            <td className="table-cell">{stall.stallName}</td>
                            <td className="table-cell">{stall.centreName}</td>
                            <td className="table-cell">{stall.rating}</td>
                            </tr>
                        ))
                        ) : (
                        <tr>
                            <td className="table-cell">-</td>
                            <td className="table-cell">-</td>
                        </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
        );
    };

export default GeographicalRegions