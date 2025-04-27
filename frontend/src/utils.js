export const regions = ['North', 'South', 'Central', 'NE', 'NW', 'SE', 'SW'];

export const assignRegion = (lat, lon) => {
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