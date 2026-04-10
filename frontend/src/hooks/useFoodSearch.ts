import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { completeFoodMacros, getFoodMacros, searchFoods } from '../services/food.service'
import type { IFood, IFoodCompleteRequest } from '../types/api.types'

const SEARCH_DEBOUNCE_MS = 300
const MIN_QUERY_LENGTH = 2
const SEARCH_STALE_MS = 5 * 60 * 1000

export function useFoodSearch() {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [query])

  const searchQuery = useQuery({
    queryKey: ['food-search', debouncedQuery],
    queryFn: () => searchFoods(debouncedQuery),
    enabled: debouncedQuery.length >= MIN_QUERY_LENGTH,
    staleTime: SEARCH_STALE_MS,
  })

  const macrosMutation = useMutation({
    mutationFn: ({ name, weight }: { name: string; weight: number }) =>
      getFoodMacros(name, weight),
  })

  const completeMutation = useMutation({
    mutationFn: (data: IFoodCompleteRequest) => completeFoodMacros(data),
  })

  function capitalize(name: string): string {
    return name.charAt(0).toUpperCase() + name.slice(1)
  }

  const suggestions: IFood[] = (searchQuery.data?.results ?? []).map((f) => ({
    ...f,
    name: capitalize(f.name),
  }))

  return {
    query,
    setQuery,
    suggestions,
    isSearching: searchQuery.isFetching,
    fetchMacros: macrosMutation.mutateAsync,
    completeMacros: completeMutation.mutateAsync,
    isFetchingMacros: macrosMutation.isPending || completeMutation.isPending,
  }
}
