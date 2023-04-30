import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter, Routes, Route, NavLink, Outlet, useParams } from 'react-router-dom'
import { Container, Navbar, Nav, Row, Col, ToastContainer, Toast, Card, Spinner, ListGroup } from 'react-bootstrap';
import { CapturePage } from './CapturePage';
import { MQTTProvider, useMQTTState } from './MQTTContext'
import React from 'react';
import APIBackend from './RestAPI'

function App() {
  let [loaded, setLoaded] = React.useState(false)
  let [pending, setPending] = React.useState(false)
  let [error, setError] = React.useState(null)

  let [config, setConfig] = React.useState([])

  React.useEffect(() => {
    let do_load = async () => {
      setPending(true)
      let response = await APIBackend.api_get('http://' + document.location.host + '/config/config.json');
      if (response.status === 200) {
        const raw_conf = response.payload;
        console.log("config",raw_conf)
        setConfig(raw_conf)
        setLoaded(true)
      } else {
        console.log("ERROR LOADING CONFIG")
        setError("ERROR: Unable to load configuration!")
      }
    }
    if (!loaded && !pending) {
      do_load()
    }
  }, [loaded, pending])
  if (!loaded) {
    return <Container fluid="md">
      <Card className='mt-2 text-center'>
        {error !== null ? <h1>{error}</h1> : <div><Spinner></Spinner> <h2 className='d-inline'>Loading Config</h2></div>}
      </Card>
    </Container>
  } else {
    return (
      <MQTTProvider
        host={config?.mqtt?.host ?? document.location.hostname}
        port={config?.mqtt?.port ?? 9001}
        prefix={config?.mqtt?.prefix ?? []}>
        <BrowserRouter>
          <Routing config={config} />
        </BrowserRouter>
      </MQTTProvider>
    )
  }
}

function Routing(props) {
  return (
    <Routes>
      <Route path='/' element={<Base {...props} />}>
        <Route path='/locations' element={<LocationList config={props.config} />} />
        <Route path='/location/:location' element={<CapturePage {...props} />} />
        <Route index element={<CapturePage {...props} />}></Route>
      </Route>
    </Routes>
  )
}

function Base(props) {
  let { connected } = useMQTTState()
  let variant = "danger"
  let text = "Disconnected"
  if (connected) {
    variant = "success"
    text = "Connected"
  }

  let params = useParams();
  const location = params.location

  return (
    <Container fluid className="vh-100 p-0 d-flex flex-column">
      {/* <div id='header'> */}
      <Navbar sticky="top" bg="secondary" variant="dark" expand="md">
        <Container fluid>
          <Navbar.Brand href="/">
            <img
              src="/logo.svg"
              className="d-inline-block align-top"
              alt="Shoestring"
            />
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" className='mb-2' />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav variant="pills" className="me-auto">
              <BSNavLink to='/locations'>Locations</BSNavLink>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
      {/* </div> */}
      <Container fluid className="flex-grow-1 main-background px-1 pt-2 px-sm-2">
        <Row className="h-100 m-0 d-flex justify-content-center pt-4 pb-5">
          <Col md={10} lg={8}>
            <Outlet />
          </Col>
        </Row>
      </Container>
      <ToastContainer className="p-3" containerPosition={"fixed"} position={"bottom-end"}>
          <Toast className="p-1" bg={variant}>
            <strong>{text}</strong>
          </Toast>
        </ToastContainer>
    </Container>
  )
}

function BSNavLink({ children, className, ...props }) {
  return <NavLink className={({ isActive }) => (isActive ? ("nav-link active " + className) : ("nav-link " + className))} {...props}>{children}</NavLink>
}

function LocationList({ config }) {
  let items = config?.location_page?.items ?? []
  return <Container fluid="md">
    <Card className='mt-2'>
      <Card.Header className='text-center'><h1>{config?.location_page?.title}</h1></Card.Header>
      <Card.Body>
        <ListGroup>
          {items.map(item => (
            <ListGroup.Item key={item}><NavLink to={"/location/" + item}>{item}</NavLink></ListGroup.Item>
          ))}
        </ListGroup>
      </Card.Body>
    </Card>
  </Container>

}

export default App;
