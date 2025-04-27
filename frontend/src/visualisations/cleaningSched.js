import React, { useEffect, useState } from 'react';
import Chart from 'react-apexcharts';
import { getCleaningSchedule, getHawkerCentres } from '../apiService';
import { assignRegion } from '../utils';

const CleaningGanttChart = () => {
    const [cleaningSched, setCleaningSched] = useState([]);
    const [hawkerCentres, setHawkerCentres] = useState([]);
    const [selectedQuarter, setSelectedQuarter] = useState('Q1'); // Default to Q1

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await getCleaningSchedule();
                setCleaningSched(response.data);

                const response_hc = await getHawkerCentres();
                setHawkerCentres(response_hc.data);
            } catch (error) {
                console.error('Error fetching geographical data:', error);
            }
        };
        fetchData();
    }, []);

    const filteredData = cleaningSched.filter(item => item.cleaning_quarter === selectedQuarter);

    const hawkerCentresWithRegion = hawkerCentres.map(hc => ({
        ...hc,
        region: assignRegion(hc.latitude, hc.longitude)
    }));

    const groupedData = filteredData.map(item => {
        const hawkerCentre = hawkerCentresWithRegion.find(hc => hc.centre_id === item.centre_id);
        const region = hawkerCentre ? hawkerCentre.region : "unknown";
        return {
            x: item.cleaning_quarter,
            y: [
                new Date(item.cleaning_startdate).getTime(),
                new Date(item.cleaning_enddate).getTime()
            ],
            centre_name: item.centre_name,
            cleaning_quarter: item.cleaning_quarter,
            cleaning_startdate: item.cleaning_startdate,
            cleaning_enddate: item.cleaning_enddate,
            region: region
        };
    });

    const groupedByRegion = groupedData.reduce((acc, item) => {
        if (!acc[item.region]) {
            acc[item.region] = [];
        }
        acc[item.region].push(item);
        return acc;
    }, {});

    const regionColors = {
        North: '#ff5733',
        South: '#33ff57',
        Central: '#3357ff',
        NE: '#ff33a6',
        NW: '#c5c3c6',
        SE: '#ffb533',
        SW: '#33b8ff',
        unknown: '#999999'
    };

    const series = Object.keys(groupedByRegion).map(region => ({
        name: region,
        data: groupedByRegion[region],
        color: regionColors[region] || '#999999', 
    }));

    const options = {
        chart: {
            type: 'rangeBar',
            height: 450
        },
        plotOptions: {
            bar: {
                horizontal: true,
                barHeight: '50%'
            }
        },
        xaxis: {
            type: 'datetime',
            labels: {
                formatter: function(value) {
                    return new Date(value).toLocaleDateString();
                }
            }
        },
        tooltip: {
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const data = w.globals.initialSeries[seriesIndex].data[dataPointIndex];
                return `
                    <div>
                        <strong>Hawker Centre:</strong> ${data.centre_name}<br/>
                        <strong>Quarter:</strong> ${data.cleaning_quarter}<br/>
                        <strong>Region:</strong> ${data.region}<br/>
                        <strong>Start Date:</strong> ${new Date(data.cleaning_startdate).toLocaleDateString()}<br/>
                        <strong>End Date:</strong> ${new Date(data.cleaning_enddate).toLocaleDateString()}
                    </div>
                `;
            }
        },
    };

    const handleQuarterChange = (event) => {
        setSelectedQuarter(event.target.value);
    };

    return (
        <div style={{width:'80%', margin:'auto'}}>
            <h1>Cleaning Schedule Gantt Chart</h1>
        

            <select style={{width:'10%'}} value={selectedQuarter} onChange={handleQuarterChange}>
                <option value="Q1">Q1</option>
                <option value="Q2">Q2</option>
                <option value="Q3">Q3</option>
                <option value="Q4">Q4</option>
            </select>

            <Chart options={options} series={series} type="rangeBar" height={450} />

            <div style={{ display: 'flex', marginTop: '20px' }}>
                {Object.keys(regionColors).map(region => (
                    <div key={region} style={{ marginRight: '20px', display: 'flex', alignItems: 'center' }}>
                        <div style={{ width: '20px', height: '20px', backgroundColor: regionColors[region], marginRight: '5px' }}></div>
                        <span>{region}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CleaningGanttChart;
