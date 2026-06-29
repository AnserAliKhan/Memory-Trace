/* eslint-disable react/no-unknown-property */
import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import {
    Physics,
    RigidBody,
    CuboidCollider,
    useSphericalJoint,
    RapierRigidBody,
} from '@react-three/rapier';
import { Environment, Lightformer, Text, useTexture, Line } from '@react-three/drei';
import * as THREE from 'three';

interface LanyardProps {
    position?: [number, number, number];
    gravity?: [number, number, number];
    fov?: number;
    transparent?: boolean;
    frontImage?: string | null;
    backImage?: string | null;
    frontText?: string;
    backText?: string;
}

const Lanyard = React.memo(function Lanyard({
    position = [0, 0, 30],
    gravity = [0, -40, 0],
    fov = 20,
    transparent = true,
    frontImage = null,
    backImage = null,
    frontText = 'ReFound',
    backText = 'Built locally.',
}: LanyardProps) {
    const [isMobile, setIsMobile] = useState<boolean>(
        typeof window !== 'undefined' && window.innerWidth < 768
    );

    React.useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth < 768);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className="w-full h-full flex justify-center items-center bg-raised rounded-lg overflow-hidden">
            <Canvas
                camera={{ position, fov }}
                dpr={[1, isMobile ? 1.5 : 2]}
                gl={{ alpha: transparent }}
                onCreated={({ gl }) => gl.setClearColor(new THREE.Color(0x000000), transparent ? 0 : 1)}
            >
                <ambientLight intensity={Math.PI} />
                <Physics gravity={gravity} timeStep={isMobile ? 1 / 30 : 1 / 60}>
                    <Band
                        isMobile={isMobile}
                        frontImage={frontImage}
                        backImage={backImage}
                        frontText={frontText}
                        backText={backText}
                    />
                </Physics>
                <Environment blur={0.75}>
                    <Lightformer
                        intensity={2}
                        color="white"
                        position={[0, -1, 5]}
                        rotation={[0, 0, Math.PI / 3]}
                        scale={[100, 0.1, 1]}
                    />
                    <Lightformer
                        intensity={3}
                        color="white"
                        position={[-1, -1, 1]}
                        rotation={[0, 0, Math.PI / 3]}
                        scale={[100, 0.1, 1]}
                    />
                    <Lightformer
                        intensity={3}
                        color="white"
                        position={[1, 1, 1]}
                        rotation={[0, 0, Math.PI / 3]}
                        scale={[100, 0.1, 1]}
                    />
                    <Lightformer
                        intensity={10}
                        color="white"
                        position={[-10, 0, 14]}
                        rotation={[0, Math.PI / 2, Math.PI / 3]}
                        scale={[100, 10, 1]}
                    />
                </Environment>
            </Canvas>
        </div>
    );
});

export default Lanyard;

// ---- Band component ----
interface BandProps {
    isMobile: boolean;
    frontImage: string | null;
    backImage: string | null;
    frontText: string;
    backText: string;
}

function Band({
    isMobile,
    frontImage,
    backImage,
    frontText,
    backText,
}: BandProps) {
    const anchorRef = useRef<RapierRigidBody>(null!);
    const cardRef = useRef<RapierRigidBody>(null!);


    // Card dimensions
    const cardWidth = 0.9;
    const cardHeight = 1.2;
    const cardDepth = 0.04;

    useSphericalJoint(anchorRef, cardRef, [[0, -0.1, 0], [0, cardHeight / 2, 0]]);

    // Load textures if provided
    const frontTexture = frontImage ? useTexture(frontImage) : null;
    const backTexture = backImage ? useTexture(backImage) : null;

    // Track card position for the rope
    const [cardPos, setCardPos] = useState(new THREE.Vector3(0, 0.5, 0));

    useFrame(() => {
        if (cardRef.current) {
            const pos = cardRef.current.translation();
            setCardPos(new THREE.Vector3(pos.x, pos.y, pos.z));
        }
    });

    const colors = {
        cardBg: '#231c16',
        amber: '#e8a838',
        cream: '#ffedd7',
        muted: '#6c5f51',
    };

    // Rope end point (top of card)
    const ropeEnd = [
        cardPos.x,
        cardPos.y + cardHeight / 2,
        cardPos.z,
    ] as [number, number, number];

    return (
        <>
            {/* Anchor point (top) */}
            <RigidBody ref={anchorRef} type="fixed" position={[0, 2.5, 0]}>
                <mesh>
                    <sphereGeometry args={[0.05]} />
                    <meshStandardMaterial color={colors.amber} />
                </mesh>
            </RigidBody>

            {/* Card with physics */}
            <RigidBody
                ref={cardRef}
                position={[0, 0.5, 0]}
                mass={0.5}
                colliders="cuboid"
                angularDamping={0.2}
                linearDamping={0.05}
                enabledRotations={[true, true, true]}
            >
                <CuboidCollider args={[cardWidth / 2, cardHeight / 2, cardDepth / 2]} />

                <group>
                    {/* Main card body */}
                    <mesh>
                        <boxGeometry args={[cardWidth, cardHeight, cardDepth]} />
                        <meshPhysicalMaterial
                            color={colors.cardBg}
                            roughness={0.4}
                            metalness={0.1}
                            clearcoat={isMobile ? 0 : 1}
                            clearcoatRoughness={0.15}
                        />
                    </mesh>

                    {/* Front face – amber glow border */}
                    <mesh position={[0, 0, cardDepth / 2 + 0.001]}>
                        <planeGeometry args={[cardWidth * 0.9, cardHeight * 0.9]} />
                        <meshPhysicalMaterial
                            color={colors.amber}
                            roughness={0.2}
                            metalness={0.8}
                            emissive={colors.amber}
                            emissiveIntensity={0.05}
                            transparent
                            opacity={0.15}
                        />
                    </mesh>

                    {/* Front content: image or text */}
                    {frontTexture ? (
                        <mesh position={[0, 0, cardDepth / 2 + 0.002]}>
                            <planeGeometry args={[cardWidth * 0.8, cardHeight * 0.7]} />
                            <meshBasicMaterial map={frontTexture} />
                        </mesh>
                    ) : (
                        <>
                            <Text
                                position={[0, 0.15, cardDepth / 2 + 0.002]}
                                fontSize={0.2}
                                color={colors.cream}
                                font="https://cdn.jsdelivr.net/npm/@fontsource/inter/files/inter-latin-700-normal.woff"   // changed from fontFamily
                                fontWeight="bold"
                                anchorX="center"
                                anchorY="middle"
                                letterSpacing={0.05}
                            >
                                {frontText}
                            </Text>
                            <Text
                                position={[0, -0.15, cardDepth / 2 + 0.002]}
                                fontSize={0.07}
                                color={colors.muted}
                                 font="https://cdn.jsdelivr.net/npm/@fontsource/inter/files/inter-latin-400-normal.woff"
                                anchorX="center"
                                anchorY="middle"
                                letterSpacing={0.1}
                            >
                                LOCAL · PRIVATE
                            </Text>
                        </>
                    )}

                    {/* Back face */}
                    <mesh position={[0, 0, -cardDepth / 2 - 0.001]} rotation={[0, Math.PI, 0]}>
                        <planeGeometry args={[cardWidth * 0.85, cardHeight * 0.85]} />
                        <meshPhysicalMaterial
                            color={colors.muted}
                            roughness={0.6}
                            metalness={0.1}
                            transparent
                            opacity={0.15}
                        />
                    </mesh>

                    {/* Back content: image or text */}
                    {backTexture ? (
                        <mesh position={[0, 0, -cardDepth / 2 - 0.002]} rotation={[0, Math.PI, 0]}>
                            <planeGeometry args={[cardWidth * 0.8, cardHeight * 0.7]} />
                            <meshBasicMaterial map={backTexture} />
                        </mesh>
                    ) : (
                        <>
                            <Text
                                position={[0, 0.1, -cardDepth / 2 - 0.002]}
                                fontSize={0.14}
                                color={colors.cream}
                                font="https://cdn.jsdelivr.net/npm/@fontsource/inter/files/inter-latin-500-normal.woff"
                                fontWeight="500"
                                anchorX="center"
                                anchorY="middle"
                                rotation={[0, Math.PI, 0]}
                                letterSpacing={0.05}
                            >
                                {backText}
                            </Text>
                            <Text
                                position={[0, -0.15, -cardDepth / 2 - 0.002]}
                                fontSize={0.06}
                                color={colors.muted}
                                font="https://cdn.jsdelivr.net/npm/@fontsource/inter/files/inter-latin-400-normal.woff"
                                anchorX="center"
                                anchorY="middle"
                                rotation={[0, Math.PI, 0]}
                                letterSpacing={0.15}
                            >
                                STAYS LOCAL
                            </Text>
                        </>
                    )}
                </group>
            </RigidBody>


            {/* Rope using @react-three/drei Line */}
            <Line
                points={[
                    [0, 2.4, 0],
                    [(0 + ropeEnd[0]) / 2, (2.4 + ropeEnd[1]) / 2 - 0.2, (0 + ropeEnd[2]) / 2],
                    ropeEnd,
                ]}
                color={colors.amber}
                transparent
                opacity={0.4}
                lineWidth={1}
            />
        </>
    );
}