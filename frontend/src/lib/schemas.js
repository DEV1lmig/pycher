import { z } from "zod";

const allowedDomains = [
  "gmail.com",
  "outlook.com",
  "yahoo.com",
  "hotmail.com",
  "urbe.edu.ve",
];

function isAllowedDomain(email) {
  const domain = email.split("@")[1]?.toLowerCase();
  return allowedDomains.includes(domain);
}

// Login schema
export const loginSchema = z.object({
  username: z
    .string()
    .min(3, "El usuario es muy corto")
    .max(32, "El usuario es muy largo")
    .regex(/^[a-zA-Z0-9_.@-]+$/, "Solo letras, números y . _ @ -"),
  password: z
    .string()
    .min(8, "La contraseña debe tener al menos 8 caracteres")
    .max(64, "La contraseña es demasiado larga"),
});

// Register schema
export const registerSchema = z
  .object({
    firstName: z
      .string()
      .min(2, "El nombre es muy corto")
      .max(32, "El nombre es muy largo")
      .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$/, "Nombre inválido"),
    lastName: z
      .string()
      .min(2, "El apellido es muy corto")
      .max(32, "El apellido es muy largo")
      .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$/, "Apellido inválido"),
    username: z
      .string()
      .min(3, "El usuario es muy corto")
      .max(32, "El usuario es muy largo")
      .regex(/^[a-zA-Z0-9_.-]+$/, "Solo letras, números y . _ -"),
    email: z
      .string()
      .email("Correo inválido")
      .max(64, "El correo es muy largo")
      .refine(isAllowedDomain, {
        message: "Dominio de correo no permitido",
      }),
    password: z
      .string()
      .min(8, "La contraseña debe tener al menos 8 caracteres")
      .max(64, "La contraseña es demasiado larga")
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]).+$/,
        "Debe contener mayúsculas, minúsculas, número y símbolo"
      ),
    confirmPassword: z.string(),
    acceptTerms: z.literal(true, {
      errorMap: () => ({ message: "Debes aceptar los términos" }),
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Las contraseñas no coinciden",
    path: ["confirmPassword"],
  });
