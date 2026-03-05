import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  const user = await prisma.user.upsert({
    where: {
      email: "admin@example.com",
    },
    update: {
      name: "Admin User",
      password: "hashed_password_here",
      emailVerified: new Date(),
      headline: "Administrator",
      bio: "Default admin account",
      interests: ["admin", "manager"],
      location: "Global",
      website: "https://example.com",
      role: "ADMIN",
      hasAccess: true,
    },
    create: {
      name: "Admin User",
      email: "admin@example.com",
      password: "hashed_password_here",
      emailVerified: new Date(),
      headline: "Administrator",
      bio: "Default admin account",
      interests: ["admin", "manager"],
      location: "Global",
      website: "https://example.com",
      role: "ADMIN",
      hasAccess: true,
    },
  });
  console.log(`管理员用户已就绪: ${user.email}`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
