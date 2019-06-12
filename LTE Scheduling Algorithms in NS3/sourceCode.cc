/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
/*
 * Author: Mrinal Aich (cs16mtech11009@iith.ac.in)
 */

#include "ns3/lte-helper.h"
#include "ns3/epc-helper.h"
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/ipv4-global-routing-helper.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/lte-module.h"
#include "ns3/applications-module.h"
#include "ns3/point-to-point-helper.h"
#include "ns3/config-store.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/netanim-module.h"

using namespace ns3;

/**
 * 20 UDP applications send data to the same number of UEs which are spread across 4 ENBs from
 * the Internet(Remote Host) connected to the PGW through a 1-Gbps Point-to-Point link. 
 * Behaviour of schedulers will be analysed depending upon different speeds and data-buffers.
 */
NS_LOG_COMPONENT_DEFINE ("EpcFirstExample");

void
PrintGnuplottableUeListToFile (std::string filename)
{
  std::ofstream outFile;
  outFile.open (filename.c_str (), std::ios_base::out | std::ios_base::trunc);
  if (!outFile.is_open ())
    {
      NS_LOG_ERROR ("Can't open file " << filename);
      return;
    }
  for (NodeList::Iterator it = NodeList::Begin (); it != NodeList::End (); ++it)
    {
      Ptr<Node> node = *it;
      int nDevs = node->GetNDevices ();
      for (int j = 0; j < nDevs; j++)
        {
          Ptr<LteUeNetDevice> uedev = node->GetDevice (j)->GetObject <LteUeNetDevice> ();
          if (uedev)
            {
              Vector pos = node->GetObject<MobilityModel> ()->GetPosition ();
              outFile << "set label \"" << uedev->GetImsi ()
                      << "\" at "<< pos.x << "," << pos.y << " left font \"Helvetica,4\" textcolor rgb \"grey\" front point pt 1 ps 0.3 lc rgb \"grey\" offset 0,0"
                      << std::endl;
            }
        }
    }
}

void
PrintGnuplottableEnbListToFile (std::string filename)
{
  std::ofstream outFile;
  outFile.open (filename.c_str (), std::ios_base::out | std::ios_base::trunc);
  if (!outFile.is_open ())
    {
      NS_LOG_ERROR ("Can't open file " << filename);
      return;
    }
  for (NodeList::Iterator it = NodeList::Begin (); it != NodeList::End (); ++it)
    {
      Ptr<Node> node = *it;
      int nDevs = node->GetNDevices ();
      for (int j = 0; j < nDevs; j++)
        {
          Ptr<LteEnbNetDevice> enbdev = node->GetDevice (j)->GetObject <LteEnbNetDevice> ();
          if (enbdev)
            {
              Vector pos = node->GetObject<MobilityModel> ()->GetPosition ();
              outFile << "set label \"" << enbdev->GetCellId ()
                      << "\" at "<< pos.x << "," << pos.y
                      << " left font \"Helvetica,4\" textcolor rgb \"white\" front  point pt 2 ps 0.3 lc rgb \"white\" offset 0,0"
                      << std::endl;
            }
        }
    }
}

void printStats(FlowMonitorHelper &flowmon_helper, bool perFlowInfo)
{
	  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon_helper.GetClassifier());
	  std::string proto;
	  Ptr<FlowMonitor> monitor = flowmon_helper.GetMonitor ();
	  std::map < FlowId, FlowMonitor::FlowStats > stats = monitor->GetFlowStats();
	  double totalTimeReceiving;
	  uint64_t totalPacketsReceived, totalPacketsDropped, totalBytesReceived;

	  totalBytesReceived = 0, totalPacketsDropped = 0, totalPacketsReceived = 0, totalTimeReceiving = 0;
	  for (std::map< FlowId, FlowMonitor::FlowStats>::iterator flow = stats.begin(); flow != stats.end(); flow++)
	  {
	    Ipv4FlowClassifier::FiveTuple  t = classifier->FindFlow(flow->first);
	    switch(t.protocol)
	     {
	     case(6):
	         proto = "TCP";
	         break;
	     case(17):
	         proto = "UDP";
	         break;
	     default:
	         exit(1);
	     }
	     totalBytesReceived += (double) flow->second.rxBytes * 8;
	     totalTimeReceiving += flow->second.timeLastRxPacket.GetSeconds ();
	     totalPacketsReceived += flow->second.rxPackets;
	     totalPacketsDropped += flow->second.txPackets - flow->second.rxPackets;
	     if (perFlowInfo) {
	       std::cout << "FlowID: " << flow->first << " (" << proto << " "
	                 << t.sourceAddress << " / " << t.sourcePort << " --> "
	                 << t.destinationAddress << " / " << t.destinationPort << ")" << std::endl;
	       std::cout << "  Tx Bytes: " << flow->second.txBytes << std::endl;
	       std::cout << "  Rx Bytes: " << flow->second.rxBytes << std::endl;
	       std::cout << "  Tx Packets: " << flow->second.txPackets << std::endl;
	       std::cout << "  Rx Packets: " << flow->second.rxPackets << std::endl;
	       std::cout << "  Time LastRxPacket: " << flow->second.timeLastRxPacket.GetSeconds () << "s" << std::endl;
	       std::cout << "  Lost Packets: " << flow->second.lostPackets << std::endl;
	       std::cout << "  Pkt Lost Ratio: " << ((double)flow->second.txPackets-(double)flow->second.rxPackets)/(double)flow->second.txPackets << std::endl;
	       std::cout << "  Throughput: " << (( ((double)flow->second.rxBytes*8) / (flow->second.timeLastRxPacket.GetSeconds ()) ) / (1024)) << "Kbps" << std::endl;
	       std::cout << "  Mean{Delay}: " << (flow->second.delaySum.GetSeconds()/flow->second.rxPackets) << std::endl;
	       std::cout << "  Mean{Jitter}: " << (flow->second.jitterSum.GetSeconds()/(flow->second.rxPackets)) << std::endl;
	     }
	   }
}

int main (int argc, char *argv[])
{
  uint16_t numberOfeNodeBs = 4;
  uint16_t numberOfUEs = 20;
  double simTime = 10.0;
  double interPacketInterval = 10;
  bool fullBufferFlag = 1;
  std::string schedulerType = "ns3::RrFfMacScheduler";
  uint16_t speed = 0;

  // Command line arguments
  CommandLine cmd;
  cmd.AddValue("speed", "Speed of the UE(s) [m/sec])", speed);
  cmd.AddValue("fullBufferFlag", "Full-Buffer case of UDP Traffic", fullBufferFlag);
  cmd.AddValue("schedulerType", "Scheduler Type)", schedulerType);
  cmd.Parse(argc, argv);
 
  // Default configuration based on problem statement
  Config::SetDefault ("ns3::LteEnbNetDevice::DlBandwidth", StringValue ("50"));
  Config::SetDefault ("ns3::LteEnbNetDevice::UlBandwidth", StringValue ("50"));
  Config::SetDefault ("ns3::LteEnbPhy::TxPower", StringValue ("30"));

  NodeContainer ueNodes;
  NodeContainer enbNodes;
  enbNodes.Create(numberOfeNodeBs);
  ueNodes.Create(numberOfUEs);

  //Placing eNB
  Ptr<ListPositionAllocator> enbpositionAlloc = CreateObject<ListPositionAllocator> ();
  enbpositionAlloc->Add (Vector(1000, 1000, 0));
  enbpositionAlloc->Add (Vector(1000, 0, 0));
  enbpositionAlloc->Add (Vector(2000, 0, 0));
  enbpositionAlloc->Add (Vector(2000, 1000, 0));

  //Install ENB Mobility Model
  MobilityHelper enbMobility;
  enbMobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
  enbMobility.SetPositionAllocator(enbpositionAlloc);
  enbMobility.Install(enbNodes);

  //Install UE Mobility Model
  MobilityHelper ueMobility;
  if(speed == 0)
    ueMobility.SetMobilityModel ("ns3::RandomWalk2dMobilityModel", "Mode", StringValue ("Time"), "Time", StringValue ("0.1s"), "Speed", StringValue ("ns3::ConstantRandomVariable[Constant=0.0]"), "Bounds", RectangleValue (Rectangle (600.0, 2400.0, -400.0, 1400.0)) );
  else
    ueMobility.SetMobilityModel ("ns3::RandomWalk2dMobilityModel", "Mode", StringValue ("Time"), "Time", StringValue ("0.1s"), "Speed", StringValue ("ns3::ConstantRandomVariable[Constant=5.0]"), "Bounds", RectangleValue (Rectangle (600.0, 2400.0, -400.0, 1400.0)) );

  ueMobility.SetPositionAllocator ("ns3::RandomDiscPositionAllocator", "X", StringValue ("1000.0"), "Y", StringValue ("1000.0"), "Theta", StringValue ("ns3::UniformRandomVariable[Min=0|Max=500]"), "Rho", StringValue ("ns3::UniformRandomVariable[Min=0|Max=360]"));
  for (uint16_t iter = 0; iter < 5; iter++)
    ueMobility.Install(ueNodes.Get(iter));

  ueMobility.SetPositionAllocator ("ns3::RandomDiscPositionAllocator", "X", StringValue ("1000.0"), "Y", StringValue ("0.0"), "Theta", StringValue ("ns3::UniformRandomVariable[Min=0|Max=500]"), "Rho", StringValue ("ns3::UniformRandomVariable[Min=0|Max=360]"));
  for (uint16_t iter = 5; iter < 10; iter++)
    ueMobility.Install(ueNodes.Get(iter));

  ueMobility.SetPositionAllocator ("ns3::RandomDiscPositionAllocator", "X", StringValue ("2000.0"), "Y", StringValue ("0.0"), "Theta", StringValue ("ns3::UniformRandomVariable[Min=0|Max=500]"), "Rho", StringValue ("ns3::UniformRandomVariable[Min=0|Max=360]"));
  for (uint16_t iter = 10; iter < 15; iter++)
    ueMobility.Install(ueNodes.Get(iter));

  ueMobility.SetPositionAllocator ("ns3::RandomDiscPositionAllocator", "X", StringValue ("2000.0"), "Y", StringValue ("1000.0"), "Theta", StringValue ("ns3::UniformRandomVariable[Min=0|Max=500]"), "Rho", StringValue ("ns3::UniformRandomVariable[Min=0|Max=360]"));
  for (uint16_t iter = 15; iter < 20; iter++)
    ueMobility.Install(ueNodes.Get(iter));

  Ptr<LteHelper> lteHelper = CreateObject<LteHelper> ();
  Ptr<PointToPointEpcHelper>  epcHelper = CreateObject<PointToPointEpcHelper> ();
  lteHelper->SetEpcHelper (epcHelper);

  lteHelper->SetSchedulerType (schedulerType);

  //PGW 
  Ptr<Node> pgw = epcHelper->GetPgwNode ();
  Ptr<ListPositionAllocator> pgwpositionAlloc = CreateObject<ListPositionAllocator> ();
  pgwpositionAlloc->Add(Vector(3000,3000,0));
  MobilityHelper pgwMobility;
  pgwMobility.SetPositionAllocator(pgwpositionAlloc);
  pgwMobility.Install(pgw);

  // Create a single RemoteHost
  NodeContainer remoteHostContainer;
  remoteHostContainer.Create (1);
  Ptr<Node> remoteHost = remoteHostContainer.Get (0);
  InternetStackHelper internet;
  internet.Install (remoteHostContainer);

  Ptr<ListPositionAllocator> rHpositionAlloc = CreateObject<ListPositionAllocator> ();
  rHpositionAlloc->Add(Vector(4000,4000,0));
  MobilityHelper rhMobility;
  rhMobility.SetPositionAllocator(rHpositionAlloc);
  rhMobility.Install(remoteHostContainer);

  // Create the Internet
  PointToPointHelper p2ph;
  p2ph.SetDeviceAttribute ("DataRate", DataRateValue (DataRate ("1Gb/s")));
  p2ph.SetDeviceAttribute ("Mtu", UintegerValue (1500));
  p2ph.SetChannelAttribute ("Delay", TimeValue (Seconds (0.010)));
  NetDeviceContainer internetDevices = p2ph.Install (pgw, remoteHost);

  Ipv4AddressHelper ipv4h;
  ipv4h.SetBase ("1.0.0.0", "255.0.0.0");
  Ipv4InterfaceContainer internetIpIfaces = ipv4h.Assign (internetDevices);
  // interface 0 is localhost/pgw, 1 is the p2p device/remoteHost

  Ipv4StaticRoutingHelper ipv4RoutingHelper;
  Ptr<Ipv4StaticRouting> remoteHostStaticRouting = ipv4RoutingHelper.GetStaticRouting (remoteHost->GetObject<Ipv4> ());
  remoteHostStaticRouting->AddNetworkRouteTo (Ipv4Address ("7.0.0.0"), Ipv4Mask ("255.0.0.0"), 1);

  // Install LTE Devices to the nodes
  NetDeviceContainer enbLteDevs = lteHelper->InstallEnbDevice (enbNodes);
  NetDeviceContainer ueLteDevs = lteHelper->InstallUeDevice (ueNodes);
  
  // Add X2 Interfaces
  lteHelper->AddX2Interface (enbNodes);

  // Install the IP stack on the UEs
  internet.Install (ueNodes);
  Ipv4InterfaceContainer ueIpIface;
  ueIpIface = epcHelper->AssignUeIpv4Address (NetDeviceContainer (ueLteDevs));
  // Assign IP address to UEs, and install applications
  for (uint32_t u = 0; u < ueNodes.GetN (); ++u)
    {
      Ptr<Node> ueNode = ueNodes.Get (u);
      // Set the default gateway for the UE
      Ptr<Ipv4StaticRouting> ueStaticRouting = ipv4RoutingHelper.GetStaticRouting (ueNode->GetObject<Ipv4> ());
      ueStaticRouting->SetDefaultRoute (epcHelper->GetUeDefaultGatewayAddress (), 1);
    }

  // Attach all UEs to eNodeB
  lteHelper->Attach (ueLteDevs);

  ApplicationContainer clientApps[numberOfUEs], serverApps[numberOfUEs];
  
  UdpServerHelper udpServer (9);

  // Packet Interval [ms] - Full-buffer / Half-buffer case
  interPacketInterval = fullBufferFlag ? 1 : 10;

  for(int i_count=0; i_count < numberOfUEs; i_count++)//Installing echo server on all UE's
  {
      serverApps[i_count] = udpServer.Install (ueNodes.Get(i_count));
      serverApps[i_count].Start (Seconds (0.1) + MilliSeconds(i_count));
      serverApps[i_count].Stop (Seconds (10.0));

      UdpClientHelper udpClient (ueIpIface.GetAddress(i_count), 9);

      udpClient.SetAttribute ("MaxPackets", UintegerValue (1500000000));
      udpClient.SetAttribute ("Interval", TimeValue (MilliSeconds (interPacketInterval)));
      udpClient.SetAttribute ("PacketSize", UintegerValue (1500));

      clientApps[i_count] = udpClient.Install (remoteHostContainer); //Install echoclient on remote host
      clientApps[i_count].Start (Seconds (0.1) + MilliSeconds(i_count + 1));
      clientApps[i_count].Stop (Seconds (10.0));
  }

  lteHelper->EnableTraces ();

  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> Monitor;
  Monitor = flowmon.Install(ueNodes);
  Monitor = flowmon.Install(remoteHostContainer);

  //SINR Radio Environment Map (REM)
  Ptr<RadioEnvironmentMapHelper> remHelper;
  if (!true)
    {
      PrintGnuplottableEnbListToFile ("enbs.txt");
      PrintGnuplottableUeListToFile ("ues.txt");

      remHelper = CreateObject<RadioEnvironmentMapHelper> ();
      remHelper->SetAttribute ("ChannelPath", StringValue ("/ChannelList/1"));
      remHelper->SetAttribute ("OutputFile", StringValue ("myrem.rem"));

      remHelper->SetAttribute ("XMin", DoubleValue (500));
      remHelper->SetAttribute ("XMax", DoubleValue (2500));
      remHelper->SetAttribute ("YMin", DoubleValue (-500));
      remHelper->SetAttribute ("YMax", DoubleValue (1500));
      remHelper->SetAttribute ("Z", DoubleValue (1.5));
      remHelper->Install ();
    }
  else
    {
      Simulator::Stop (Seconds (simTime));
    }

  Simulator::Run();
  //printStats(flowmon,true);
  Simulator::Destroy();
  return 0;
}

