import React, { useState, useEffect } from 'react';
import { getReviewStatsForStall, getHawkerCentres, getHawkerStallsByCentreId } from '../apiService';
import { Card } from 'react-bootstrap';
import Select from 'react-select';
import { Wordcloud } from '@visx/wordcloud';
import { scaleLog } from '@visx/scale';
import { Text } from '@visx/text';



const ReviewStats = () => {
    const [selectedCentre, setSelectedCentre] = useState(null);
    const [selectedStall, setSelectedStall] = useState(null);
    const [stallData, setStallData] = useState(null);
    const [hawkerCentres, setHawkerCentres] = useState([]);
    const [hawkerStalls, setHawkerStalls] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                    const response_hc = await getHawkerCentres();
                    setHawkerCentres(response_hc.data);
                } catch (error) {
                    console.error('Error fetching data:', error);
                };
        };
        fetchData();
    }, []);

    const centreOptions = hawkerCentres?.map((centre) => ({
        value: centre.centre_id,
        label: centre.name,
    }));

    const stallOptions = hawkerStalls?.map((stall) => ({
        value: stall.stall_id,
        label: stall.name,
    }));

    const selectHawkerCentre = async (selectedOption) => {
        setSelectedCentre(selectedOption.value);
        try {
            const response_hs = await getHawkerStallsByCentreId(selectedOption.value);
            setHawkerStalls(response_hs.data);
        } catch (error) {
            console.error('Error fetching stalls:', error);
        }
    };

    const selectHawkerStall = async (selectedOption) => {
        setSelectedStall(selectedOption.value);
        try {
            const response = await getReviewStatsForStall(selectedOption.value);
            setStallData(response.data[0]);
        } catch (error) {
            console.error('Error fetching review stats:', error);
        }
    };

    const colors = ['#143059', '#5f76b3', '#7297b0'];

    const fontScale = stallData?.top_10_words ? scaleLog({
        domain: [
            Math.min(...stallData.top_10_words.map(([_, count]) => count)),
            Math.max(...stallData.top_10_words.map(([_, count]) => count)),
        ],
        range: [10, 100],
    }): null;


    return (
        <div style={{padding: '20px', marginTop: '20px'}}>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '20px' }}>
                <Select 
                    className="react-select"
                    options={centreOptions}
                    onChange={selectHawkerCentre}
                    placeholder="Select a Centre"
                />
                <Select 
                    className="react-select"
                    options={stallOptions}
                    onChange={selectHawkerStall}
                    placeholder="Select a Stall"
                    isSearchable={true}

                />
            </div>
            
            {stallData && (
                <div className="mt-4">
                    <br />
                    <h2>{stallData.stall_name}</h2>
                    <table style={{width:"50%", margin:"auto", borderCollapse: 'collapse'}}>
                        <tbody>
                            <tr style={{ backgroundColor: '#f0f0f0' }}>
                                <th className="table-cell">Number of Reviews</th>
                                <th className="table-cell">Number of Authors</th>
                                <th className="table-cell">Average User Rating</th>
                                <th className="table-cell">Standard Deviation of Rating</th>
                                <th className="table-cell">Average Number of Visits</th>
                            </tr>
                            <tr>
                                <td className="table-cell">{stallData.no_of_reviews}</td>
                                <td className="table-cell">{stallData.no_of_authors}</td>
                                <td className="table-cell">{stallData.avg_user_rating}</td>
                                <td className="table-cell">{stallData.rating_sd}</td>
                                <td className="table-cell">{stallData.avg_no_of_visits}</td>
                            </tr>
                        </tbody>
                        </table>

                    {stallData?.top_10_words && (
                        <div className="mt-4" style={{ height: '400px', width: '100%' }}>
                            <h3>Top 10 Keywords</h3>
                            <Wordcloud
                                words={stallData.top_10_words.map(([text, count]) => ({
                                    text,
                                    value: count,
                                }))}
                                width={500}
                                height={300}
                                fontSize={(datum) => fontScale(datum.value)}
                                font={'Impact'}
                                padding={2}
                                spiral={'archimedean'}
                                rotate={0}
                                random={() => 0.5}
                                >
                                {(cloudWords) =>
                                    cloudWords.map((w, i) => (
                                    <Text
                                        key={w.text}
                                        fill={colors[i % colors.length]}
                                        textAnchor="middle"
                                        transform={`translate(${w.x}, ${w.y}) rotate(${w.rotate})`}
                                        fontSize={w.size}
                                        fontFamily={w.font}
                                    >
                                        {w.text}
                                    </Text>
                                    ))
                                }
                                </Wordcloud>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ReviewStats;
