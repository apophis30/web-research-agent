# Web Research Agent Frontend

This is the frontend application for the Web Research Agent project, built with [Next.js](https://nextjs.org).

## Local Development

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

## AWS EC2 Deployment (Free Tier)

### Prerequisites
- AWS EC2 Linux instance (Free Tier)
- SSH access to the instance

### Deployment Steps

1. Clone the repository:
```bash
git clone -b frontend https://github.com/apophis30/web-research-agent.git
```

2. Update system packages:
```bash
sudo apt update
sudo apt upgrade -y
```

3. Install Node.js:
```bash
sudo apt install nodejs npm -y
```

4. Build the application:
```bash
npm install
npm run build
```

5. Install and configure PM2 for process management:
```bash
sudo npm install -g pm2
pm2 start npm --name "web-research-agent" -- start
```

### PM2 Commands
- View running processes: `pm2 list`
- View logs: `pm2 logs web-research-agent`
- Restart application: `pm2 restart web-research-agent`
- Stop application: `pm2 stop web-research-agent`

## Additional Information

- The application uses Next.js for server-side rendering and static site generation
- Built with TypeScript for type safety
- Uses modern React features and best practices
- Optimized for performance and SEO

## Project Structure

```
src/
├── app/
│   ├── page.tsx        # Main application page
│   └── layout.tsx      # Root layout component
├── components/
│   ├── ui/            # shadcn utility components
│   ├── NewsTab.tsx
│   ├── ResearchTab.tsx
│   ├── Sidebar.tsx
│   ├── WebpageScraper.tsx
│   └── WebSearchTab.tsx
├── hooks/             # Custom React hooks
├── lib/               # Shadcn utility functions & configurations
└── utils/
    └── api.ts         # utility function for making API requests
```
