import axiosClient from './axiosClient';

export const getGeographicalData = () => axiosClient.get('/geographicalData');

export const getHawkerCentres = () => axiosClient.get('/hawkerCentres');

export const getHawkerStallsByCentreId = (centreId) => axiosClient.get(`/hawkerStallByCentreId?centreId=${centreId}`);

export const getReviewStatsForStall = (stallId) => axiosClient.get(`/reviewsDataForStall?stallId=${stallId}`);

export const getCleaningSchedule = () => axiosClient.get('/cleaningSchedule');