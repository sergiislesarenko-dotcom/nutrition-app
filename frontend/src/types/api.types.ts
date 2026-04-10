// Mirrors api_contracts.md schemas exactly

export interface IFood {
  id: number
  name: string
  calories_per_100g: number
  protein_per_100g: number
  carbs_per_100g: number
  fat_per_100g: number
}

export interface IFoodSearchResponse {
  results: IFood[]
}

export interface IFoodMacrosResponse {
  food: IFood
  weight_g: number
  calories_kcal: number
  protein_g: number
  carbs_g: number
  fat_g: number
}

export interface IKnownMacros {
  calories_per_100g?: number
  protein_per_100g?: number
  carbs_per_100g?: number
  fat_per_100g?: number
}

export interface IFoodCompleteRequest {
  name: string
  weight_g: number
  known: IKnownMacros
}

export interface IUserOut {
  id: number
  email: string
  age: number
  weight_kg: number
  height_cm: number
  gender: string
  activity_level: string
  bmi: number
  tdee: number
  created_at: string
}

export interface IAuthResponse {
  user: IUserOut
  access_token: string
  token_type: 'bearer'
}

export interface ILoginRequest {
  email: string
  password: string
}

export interface IRegisterRequest {
  email: string
  password: string
  age: number
  weight_kg: number
  height_cm: number
  gender: 'male' | 'female' | 'other'
  activity_level: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active'
}

export interface INutritionLog {
  id: number
  user_id: number
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  food_name: string
  weight_g: number
  calories_kcal: number
  protein_g: number
  carbs_g: number
  fat_g: number
  logged_at: string
}

export interface IAddLogRequest {
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  food_name: string
  weight_g: number
  calories_kcal: number
  protein_g: number
  carbs_g: number
  fat_g: number
  logged_at?: string
}

export interface IDaySummary {
  total_calories: number
  total_protein: number
  total_carbs: number
  total_fat: number
  goal_calories: number | null
  deficit_surplus: number | null
}

export interface ILogsResponse {
  logs: INutritionLog[]
  summary: IDaySummary
}

export interface IGoal {
  id: number
  goal_type: 'weight_loss' | 'muscle_gain' | 'maintenance' | 'health'
  target_weight_kg: number | null
  daily_calories_kcal: number | null
  deadline: string | null
  is_active: boolean
}

export interface IGoalCreate {
  goal_type: 'weight_loss' | 'muscle_gain' | 'maintenance' | 'health'
  target_weight_kg?: number
  daily_calories_kcal?: number
  deadline?: string
}

export interface IRestriction {
  id: number
  type: 'dietary' | 'medical' | 'allergy'
  value: string
}

export interface IRestrictionCreate {
  type: 'dietary' | 'medical' | 'allergy'
  value: string
}

export interface IRecommendation {
  id: number
  question: string
  answer: string
  created_at: string
}

export interface IRecommendationsResponse {
  items: IRecommendation[]
  total: number
}

export interface IChatResponse {
  answer: string
  recommendation_id: number
}

export interface IApiError {
  detail: string
  code: string | null
}
