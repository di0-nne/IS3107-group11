import axiosClient from './axiosClient';

export const getGeographicalData = () => axiosClient.get('/geographicalData');

// export const postUser = (userData) =>
//     axiosClient.post('/geographicalData', userData);

// export const getUserById = (id) =>
//     axiosClient.get(`/api/users/${id}`);

// export const updateUser = (id, userData) =>
//     axiosClient.put(`/api/users/${id}`, userData);

// export const deleteUser = (id) =>
//     axiosClient.delete(`/api/users/${id}`);