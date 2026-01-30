import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  await prisma.user.create({
    data: {
      id: "01",
      name: 'Admin User',
      email: 'admin@example.com',
      password: 'hashed_password_here',
      emailVerified: new Date(),
      headline: 'Administrator',
      bio: 'Default admin account',
      interests: ['admin', 'manager'],
      location: 'Global',
      website: 'https://example.com',
      role: 'ADMIN',
      hasAccess: true,
    },
  });
  console.log('插入第一个测试用户插入成功');
}

main()
  .catch(e => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });