'use client'

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { 
  Sheet, 
  SheetContent, 
  SheetHeader, 
  SheetTitle, 
  SheetTrigger 
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Menu } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { useMediaQuery } from "@/hooks/useMediaQuery"
import { useState, useEffect, ChangeEvent } from "react"

export interface ApiConfig {
  apiUrl: string;
  userId: string;
}

interface SidebarProps {
  apiConfig: ApiConfig;
  setApiConfig: (config: ApiConfig) => void;
}

export function Sidebar({ apiConfig, setApiConfig }: SidebarProps) {
  const [open, setOpen] = useState(false)
  const isDesktop = useMediaQuery("(min-width: 768px)")
  
  // Close sheet when resizing to desktop
  useEffect(() => {
    if (isDesktop) {
      setOpen(false)
    }
  }, [isDesktop])

  const handleApiUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
    setApiConfig({
      ...apiConfig,
      apiUrl: e.target.value
    });
  };

  const handleUserIdChange = (e: ChangeEvent<HTMLInputElement>) => {
    setApiConfig({
      ...apiConfig,
      userId: e.target.value
    });
  };

  const sidebarContent = (
    <div className="h-full py-6 px-4 flex flex-col">
      <h2 className="text-2xl font-bold mb-2">Web Research Assistant</h2>
      <Separator className="mb-6" />
      
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="api-url">API URL</Label>
          <Input 
            id="api-url" 
            value={apiConfig.apiUrl} 
            onChange={handleApiUrlChange}
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="user-id">User ID (optional)</Label>
          <Input 
            id="user-id" 
            value={apiConfig.userId} 
            onChange={handleUserIdChange}
          />
        </div>
      </div>
      
      <Separator className="my-6" />
      
      <div className="mt-auto">
        <h3 className="font-semibold mb-2">About</h3>
        <p className="text-sm text-gray-600">
          This application lets you perform web research, search for information, 
          scrape webpages, and analyze content.
        </p>
      </div>
    </div>
  )

  // For mobile: show as a sheet
  // For desktop: show as a sidebar
  return (
    <>
      {isDesktop ? (
        <div className="w-80 border-r bg-gray-50/50 h-full hidden md:block overflow-y-auto">
          {sidebarContent}
        </div>
      ) : (
        <>
          <div className="fixed left-4 top-4 z-40">
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-80 sm:w-96">
                <SheetHeader>
                  <SheetTitle>Web Research Assistant</SheetTitle>
                </SheetHeader>
                {sidebarContent}
              </SheetContent>
            </Sheet>
          </div>
        </>
      )}
    </>
  )
}