import { z } from 'zod';
export const ideaSchema = z.object({ title: z.string().trim().min(1).max(120), description: z.string().trim().min(10).max(5000) });
export const planSchema = z.object({ ideaId: z.string().cuid() });
