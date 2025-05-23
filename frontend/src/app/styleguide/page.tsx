"use client"

import * as React from "react"
import { 
  Button, 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent, 
  Badge,
  Modal,
  useModal,
  ConfirmDialog,
  useConfirmDialog,
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  TableEmpty,
  TableLoading,
  ThemeToggle,
  ThemeSelector,
} from "@/components/ui"
import { 
  Palette, 
  Type, 
  Square, 
  Grid3X3, 
  Navigation, 
  Settings,
  Users,
  FileText,
  BarChart3,
  Search,
  Plus,
  Edit,
  Trash2
} from "lucide-react"

export default function StyleGuidePage() {
  const exampleModal = useModal()
  const confirmDialog = useConfirmDialog()
  const [tableLoading, setTableLoading] = React.useState(false)
  const [showTableEmpty, setShowTableEmpty] = React.useState(false)

  const handleDeleteExample = async () => {
    const confirmed = await confirmDialog.confirm({
      title: "Elimina elemento di esempio",
      description: "Sei sicuro di voler eliminare questo elemento? Questa azione non può essere annullata.",
      confirmText: "Elimina",
      itemName: "Elemento Demo",
      onConfirm: async () => {
        // Simula una chiamata API
        await new Promise(resolve => setTimeout(resolve, 2000))
        console.log("Elemento eliminato!")
      }
    })
    
    if (confirmed) {
      console.log("Eliminazione confermata")
    }
  }

  const handleTableLoading = () => {
    setTableLoading(true)
    setTimeout(() => setTableLoading(false), 3000)
  }

  const exampleTableData = [
    { id: 1, name: "ODL-001", status: "active", priority: "alta", date: "2024-01-15" },
    { id: 2, name: "ODL-002", status: "completed", priority: "media", date: "2024-01-14" },
    { id: 3, name: "ODL-003", status: "pending", priority: "bassa", date: "2024-01-13" },
  ]

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 space-y-12">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Design System</h1>
            <p className="text-muted-foreground">
              Guida ai componenti UI di CarbonPilot
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <ThemeSelector />
          </div>
        </div>

        {/* Palette Colori */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Palette className="mr-2 h-5 w-5" />
                Palette Colori
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Colori Primari */}
              <div>
                <h4 className="font-medium mb-3">Colori Primari</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <div className="h-16 bg-primary rounded-lg"></div>
                    <p className="text-sm font-medium">Primary</p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-16 bg-secondary rounded-lg"></div>
                    <p className="text-sm font-medium">Secondary</p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-16 bg-accent rounded-lg"></div>
                    <p className="text-sm font-medium">Accent</p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-16 bg-muted rounded-lg"></div>
                    <p className="text-sm font-medium">Muted</p>
                  </div>
                </div>
              </div>

              {/* Colori di Stato */}
              <div>
                <h4 className="font-medium mb-3">Colori di Stato</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <div className="h-16 bg-success rounded-lg"></div>
                    <p className="text-sm font-medium">Success</p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-16 bg-warning rounded-lg"></div>
                    <p className="text-sm font-medium">Warning</p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-16 bg-destructive rounded-lg"></div>
                    <p className="text-sm font-medium">Error</p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-16 bg-info rounded-lg"></div>
                    <p className="text-sm font-medium">Info</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Tipografia */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Type className="mr-2 h-5 w-5" />
                Tipografia
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h1>Heading 1 - Text 3xl</h1>
                <h2>Heading 2 - Text 2xl</h2>
                <h3>Heading 3 - Text xl</h3>
                <h4>Heading 4 - Text lg</h4>
                <h5>Heading 5 - Text base</h5>
                <h6>Heading 6 - Text sm</h6>
                <p>Paragrafo normale con font sans-serif elegante e spaziatura ottimale per la lettura.</p>
                <small>Testo piccolo per note e informazioni secondarie.</small>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Bottoni */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Square className="mr-2 h-5 w-5" />
                Bottoni
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Varianti */}
              <div>
                <h4 className="font-medium mb-3">Varianti</h4>
                <div className="flex flex-wrap gap-3">
                  <Button variant="default">Default</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="destructive">Destructive</Button>
                  <Button variant="success">Success</Button>
                  <Button variant="warning">Warning</Button>
                  <Button variant="info">Info</Button>
                </div>
              </div>

              {/* Dimensioni */}
              <div>
                <h4 className="font-medium mb-3">Dimensioni</h4>
                <div className="flex flex-wrap items-center gap-3">
                  <Button size="sm">Small</Button>
                  <Button size="default">Default</Button>
                  <Button size="lg">Large</Button>
                  <Button size="icon"><Plus className="h-4 w-4" /></Button>
                </div>
              </div>

              {/* Stati */}
              <div>
                <h4 className="font-medium mb-3">Stati</h4>
                <div className="flex flex-wrap gap-3">
                  <Button>Normale</Button>
                  <Button loading>Loading</Button>
                  <Button disabled>Disabilitato</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Badge */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Badge className="mr-2">Badge</Badge>
                Badge
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Badge variant="default">Default</Badge>
                <Badge variant="secondary">Secondary</Badge>
                <Badge variant="success">Success</Badge>
                <Badge variant="warning">Warning</Badge>
                <Badge variant="error">Error</Badge>
                <Badge variant="info">Info</Badge>
                <Badge variant="pending">Pending</Badge>
                <Badge variant="active">Active</Badge>
                <Badge variant="completed">Completed</Badge>
                <Badge variant="cancelled">Cancelled</Badge>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Card Varianti */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle>Card Varianti</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card variant="default">
                  <CardHeader>
                    <CardTitle>Default Card</CardTitle>
                  </CardHeader>
                  <CardContent>
                    Con ombra soft e bordi rounded.
                  </CardContent>
                </Card>

                <Card variant="elevated">
                  <CardHeader>
                    <CardTitle>Elevated Card</CardTitle>
                  </CardHeader>
                  <CardContent>
                    Con ombra più marcata senza bordi.
                  </CardContent>
                </Card>

                <Card variant="outline">
                  <CardHeader>
                    <CardTitle>Outline Card</CardTitle>
                  </CardHeader>
                  <CardContent>
                    Con bordo marcato e ombra minima.
                  </CardContent>
                </Card>

                <Card variant="flat">
                  <CardHeader>
                    <CardTitle>Flat Card</CardTitle>
                  </CardHeader>
                  <CardContent>
                    Senza ombra con background muted.
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Tabelle */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Grid3X3 className="mr-2 h-5 w-5" />
                Tabelle
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Button onClick={handleTableLoading} size="sm">
                  Test Loading
                </Button>
                <Button 
                  onClick={() => setShowTableEmpty(!showTableEmpty)} 
                  size="sm" 
                  variant="outline"
                >
                  Toggle Empty
                </Button>
              </div>

              {tableLoading ? (
                <div className="border rounded-2xl">
                  <TableLoading />
                </div>
              ) : showTableEmpty ? (
                <div className="border rounded-2xl">
                  <TableEmpty 
                    message="Nessun ODL trovato"
                    action={{
                      label: "Crea nuovo ODL",
                      onClick: () => console.log("Crea ODL")
                    }}
                  />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome ODL</TableHead>
                      <TableHead>Stato</TableHead>
                      <TableHead>Priorità</TableHead>
                      <TableHead>Data</TableHead>
                      <TableHead>Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {exampleTableData.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">{item.name}</TableCell>
                        <TableCell>
                          <Badge variant={
                            item.status === "active" ? "active" :
                            item.status === "completed" ? "completed" : "pending"
                          }>
                            {item.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={
                            item.priority === "alta" ? "error" :
                            item.priority === "media" ? "warning" : "info"
                          }>
                            {item.priority}
                          </Badge>
                        </TableCell>
                        <TableCell>{item.date}</TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button size="icon" variant="ghost">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button size="icon" variant="ghost" onClick={handleDeleteExample}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </section>

        {/* Modal e Dialog */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle>Modal e Dialog</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Button onClick={exampleModal.openModal}>
                  Apri Modal Esempio
                </Button>
                <Button onClick={handleDeleteExample} variant="destructive">
                  Test Confirm Dialog
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Spaziature */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle>Spaziature e Utility</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <p className="font-medium">Spaziature:</p>
                <div className="flex flex-wrap gap-2">
                  <div className="spacing-xs bg-muted rounded">spacing-xs</div>
                  <div className="spacing-sm bg-muted rounded">spacing-sm</div>
                  <div className="spacing-md bg-muted rounded">spacing-md</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <p className="font-medium">Ombre:</p>
                <div className="grid grid-cols-3 gap-4">
                  <div className="h-16 bg-card shadow-card rounded-2xl flex items-center justify-center">
                    shadow-card
                  </div>
                  <div className="h-16 bg-card shadow-soft rounded-2xl flex items-center justify-center">
                    shadow-soft  
                  </div>
                  <div className="h-16 bg-card shadow-modal rounded-2xl flex items-center justify-center">
                    shadow-modal
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Modal Example */}
        <Modal
          open={exampleModal.open}
          onOpenChange={exampleModal.setOpen}
          title="Modal di Esempio"
          description="Questo è un modal di esempio per testare il design system."
          size="md"
          onConfirm={() => {
            console.log("Confermato!")
            exampleModal.closeModal()
          }}
          onCancel={exampleModal.closeModal}
        >
          <div className="space-y-4">
            <p>Contenuto del modal con form o informazioni.</p>
            <div className="flex gap-2">
              <Button size="sm">Azione 1</Button>
              <Button size="sm" variant="outline">Azione 2</Button>
            </div>
          </div>
        </Modal>

        {/* Confirm Dialog */}
        <confirmDialog.ConfirmDialog />
      </div>
    </div>
  )
} 