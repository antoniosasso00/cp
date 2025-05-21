import { useQuery, useMutation, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';

const api = axios.create({
  baseURL: '/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export function useApiQuery<TData = unknown, TError = AxiosError>(
  key: string[],
  url: string,
  options?: UseQueryOptions<TData, TError>
) {
  return useQuery<TData, TError>({
    queryKey: key,
    queryFn: async () => {
      const { data } = await api.get<TData>(url);
      return data;
    },
    ...options,
  });
}

export function useApiMutation<TData = unknown, TVariables = unknown, TError = AxiosError>(
  url: string,
  options?: UseMutationOptions<TData, TError, TVariables>
) {
  return useMutation<TData, TError, TVariables>({
    mutationFn: async (variables) => {
      const { data } = await api.post<TData>(url, variables);
      return data;
    },
    ...options,
  });
}

export function useApiUpdate<TData = unknown, TVariables = unknown, TError = AxiosError>(
  url: string,
  options?: UseMutationOptions<TData, TError, TVariables>
) {
  return useMutation<TData, TError, TVariables>({
    mutationFn: async (variables) => {
      const { data } = await api.put<TData>(url, variables);
      return data;
    },
    ...options,
  });
}

export function useApiDelete<TError = AxiosError>(
  url: string,
  options?: UseMutationOptions<void, TError, void>
) {
  return useMutation<void, TError, void>({
    mutationFn: async () => {
      await api.delete(url);
    },
    ...options,
  });
} 