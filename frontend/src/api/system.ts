import { api } from './client';
export const systemApi = {
  dataSources: ()=> api.get<any>('/api/v1/system/data-sources'),
  models: ()=> api.get<any>('/api/v1/system/models'),
  health: ()=> api.get<any>('/api/v1/system/health'),
};
